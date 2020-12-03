#!/usr/bin/env python3

from notify_deps import *

import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template

log_local = get_logger('email')

EMAIL_TEMPLATE = Template(open('templates/base.html').read())

NUVLA_API_LOCAL = 'http://api:8200'


def get_nuvla_config():
    nuvla_api_authn_header = 'group/nuvla-admin'
    config_url = f'{NUVLA_API_LOCAL}/api/configuration/nuvla'
    headers = {'nuvla-authn-info': nuvla_api_authn_header}
    resp = requests.get(config_url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f'Failed to get response from server: status {resp.status_code}')
    return resp.json()


try:
    if 'SMTP_HOST' in os.environ:
        SMTP_HOST = os.environ['SMTP_HOST']
        SMTP_USER = os.environ['SMTP_USER']
        SMTP_PASSWORD = os.environ['SMTP_PASSWORD']
        SMTP_PORT = int(os.environ['SMTP_PORT'])
        SMTP_SSL = os.environ['SMTP_SSL'].lower() in ['true', 'True']
    else:
        nuvla_config = get_nuvla_config()
        SMTP_HOST = nuvla_config['smtp-host']
        SMTP_USER = nuvla_config['smtp-username']
        SMTP_PASSWORD = nuvla_config['smtp-password']
        SMTP_PORT = nuvla_config['smtp-port']
        SMTP_SSL = nuvla_config['smtp-ssl']
except Exception as ex:
    msg = f'Provide full SMTP config either via env vars or in configuration/nuvla: {ex}'
    log_local.error(msg)
    raise Exception(msg)

KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_EMAIL_S'
KAFKA_GROUP_ID = 'nuvla-notification-email'

SEND_EMAIL_ATTEMPTS = 3


def get_smtp_server(debug_level=0):
    if SMTP_SSL:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.set_debuglevel(debug_level)
    log_local.info('SMTP initialised.')
    return server


def send(server, recipients, subject, message, attempts=SEND_EMAIL_ATTEMPTS):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = server.user
    msg['To'] = ', '.join(recipients)
    html = EMAIL_TEMPLATE.render(title=subject,
                                 message=message,
                                 conditions_url=f"{NUVLA_ENDPOINT}/terms")
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    for i in range(attempts):
        try:
            resp = server.sendmail(server.user, recipients, msg.as_string())
            if resp:
                log_local.error(f'SMTP failed to deliver email to: {resp}')
            return
        except smtplib.SMTPSenderRefused as ex:
            log_local.warning(f'Failed sending email: {ex}')
            time.sleep(.25)
            log_local.warning(f'Failed sending email: retry {i}')
    log_local.error(f'Failed sending email after {attempts} attempts.')


def worker(workq: multiprocessing.Queue):
    smtp_server = get_smtp_server()
    while True:
        msg = workq.get()
        if msg:
            recipients = msg.value['DESTINATION'].split(',')
            r_id = msg.value['RESOURCE_ID']
            r_state = msg.value['RESOURCE_STATE']
            m = f'<a href="{NUVLA_ENDPOINT.rstrip("/")}/ui/api/{r_id}">{r_id}</a> in state <b>{r_state}</b>'
            subject = 'nuvla notification'
            send(smtp_server, recipients, subject, m)
            log_local.info(f'sent: {m} to {recipients}')


if __name__ == "__main__":
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID)
