#!/usr/bin/env python3

import multiprocessing
import os
import requests
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from datetime import datetime

from notify_deps import get_logger, timestamp_convert, main
from notify_deps import NUVLA_ENDPOINT


log_local = get_logger('email')

EMAIL_TEMPLATE_FILE = 'templates/base.html'
EMAIL_TEMPLATE = Template('')

NUVLA_API_LOCAL = 'http://api:8200'

SMTP_HOST = SMTP_USER = SMTP_PASSWORD = SMTP_PORT = SMTP_SSL = ''

IMG_ALERT_OK = 'ui/images/nuvla-alert-ok.png'
IMG_ALERT_NOK = 'ui/images/nuvla-alert-nok.png'


class SendFailedMaxAttempts(Exception):
    pass


def get_nuvla_config():
    nuvla_api_authn_header = 'group/nuvla-admin'
    config_url = f'{NUVLA_API_LOCAL}/api/configuration/nuvla'
    headers = {'nuvla-authn-info': nuvla_api_authn_header}
    resp = requests.get(config_url, headers=headers)
    if resp.status_code != 200:
        raise EnvironmentError(f'Failed to get response from server: status {resp.status_code}')
    return resp.json()


def set_smpt_params():
    global SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_PORT, SMTP_SSL
    try:
        if 'SMTP_HOST' in os.environ:
            SMTP_HOST = os.environ['SMTP_HOST']
            SMTP_USER = os.environ['SMTP_USER']
            SMTP_PASSWORD = os.environ['SMTP_PASSWORD']
            try:
                SMTP_PORT = int(os.environ['SMTP_PORT'])
            except ValueError:
                raise ValueError(f"Incorrect value for SMTP_PORT number: {os.environ['SMTP_PORT']}")
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
        raise ValueError(msg)


KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_EMAIL_S'
KAFKA_GROUP_ID = 'nuvla-notification-email'

SEND_EMAIL_ATTEMPTS = 3


def get_smtp_server(debug_level=0) -> smtplib.SMTP:
    if SMTP_SSL:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.set_debuglevel(debug_level)
    log_local.info('SMTP initialised.')
    return server


def html_content(values: dict):
    subs_config_link = f'<a href="{NUVLA_ENDPOINT}/ui/notifications">Notification configuration</a>'

    r_uri = values.get('RESOURCE_URI')
    r_name = values.get('RESOURCE_NAME')
    component_link = f'<a href="{NUVLA_ENDPOINT}/ui/{r_uri}">{r_name or r_uri}</a>'
    metric = values.get('METRIC')
    condition = values.get('CONDITION')
    if values.get('RECOVERY', False):
        img_alert = IMG_ALERT_OK
        title = f"[OK] {values.get('SUBS_NAME')}"
    else:
        img_alert = IMG_ALERT_NOK
        title = f"[Alert] {values.get('SUBS_NAME')}"
    params = {
        'title': title,
        'subs_description': values.get('SUBS_DESCRIPTION'),
        'component_link': component_link,
        'metric': metric,
        'condition': condition.upper(),
        'timestamp': timestamp_convert(values.get('TIMESTAMP')),
        'subs_config_link': subs_config_link,
        'header_img': f'{NUVLA_ENDPOINT}/{img_alert}',
        'current_year': str(datetime.now().year)
    }
    if values.get('VALUE'):
        params['condition'] = f"{values.get('CONDITION')} {values.get('CONDITION_VALUE')}"
        params['value'] = values.get('VALUE')
    return EMAIL_TEMPLATE.render(**params)


def send(server: smtplib.SMTP, recipients, subject, html, attempts=SEND_EMAIL_ATTEMPTS):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'Nuvla <{server.user}>'
    msg['To'] = ', '.join(recipients)
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    for i in range(attempts):
        if i > 0:
            log_local.warning(f'Failed sending email: retry {i}')
            time.sleep(.5)
            log_local.warning(f'Reconnecting to SMTP server...')
            server = get_smtp_server()
            log_local.warning(f'Reconnecting to SMTP server... done.')
        try:
            resp = server.sendmail(server.user, recipients, msg.as_string())
            if resp:
                log_local.error(f'SMTP failed to deliver email to: {resp}')
            return
        except smtplib.SMTPException as ex:
            log_local.error(f'Failed sending email due to SMTP error: {ex}')
    raise SendFailedMaxAttempts(f'Failed sending email after {attempts} attempts.')


def get_recipients(v: dict):
    return list(filter(lambda x: x != '', v.get('DESTINATION', '').split(' ')))


def worker(workq: multiprocessing.Queue):
    smtp_server = get_smtp_server()
    while True:
        msg = workq.get()
        if msg:
            recipients = get_recipients(msg.value)
            if len(recipients) == 0:
                log_local.warning(f'No recipients provided in: {msg.value}')
                continue
            r_id = msg.value.get('RESOURCE_ID')
            r_name = msg.value.get('NAME')
            subject = msg.value.get('SUBS_NAME') or f'{r_name or r_id} alert'
            try:
                html = html_content(msg.value)
                send(smtp_server, recipients, subject, html)
                log_local.info(f'sent: {msg} to {recipients}')
            except smtplib.SMTPException as ex:
                log_local.error(f'Failed sending email due to SMTP error: {ex}')
                log_local.warning(f'Reconnecting to SMTP server...')
                smtp_server = get_smtp_server()
                log_local.warning(f'Reconnecting to SMTP server... done.')
            except Exception as ex:
                log_local.error(f'Failed sending email: {ex}')


if __name__ == "__main__":
    EMAIL_TEMPLATE = Template(open(EMAIL_TEMPLATE_FILE).read())
    set_smpt_params()
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID)
