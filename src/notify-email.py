#!/usr/bin/env python3

import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml
import multiprocessing
import requests
import smtplib
from jinja2 import Template
from datetime import datetime

from notify_deps import get_logger, timestamp_convert, main
from notify_deps import NUVLA_ENDPOINT, prometheus_exporter_port
from prometheus_client import start_http_server
from metrics import (PROCESS_STATES, NOTIFICATIONS_SENT, NOTIFICATIONS_ERROR,
                     registry)
from xoauth2_client import (SMTPParams, SMTPParamsGoogle, XOAuth2SMTPClient,
                            XOAuth2SMTPClientGoogle)


log_local = get_logger('email')

EMAIL_TEMPLATE_DEFAULT_FILE = 'templates/default.html'
EMAIL_TEMPLATE_APP_PUB_FILE = 'templates/app-pub.html'

EMAIL_TEMPLATES = {
    'default': Template('dummy'),
    'app-pub': Template('dummy'),
}

NUVLA_API_LOCAL = 'http://api:8200'

SMTP_CONFIG_ENV = 'SMTP_CONFIG'

IMG_ALERT_OK = 'ui/images/nuvla-alert-ok.png'
IMG_ALERT_NOK = 'ui/images/nuvla-alert-nok.png'


class SendFailedMaxAttempts(Exception):
    pass


def get_smtp_config_from_nuvla() -> dict:
    nuvla_api_authn_header = 'group/nuvla-admin'
    config_url = f'{NUVLA_API_LOCAL}/api/configuration/nuvla'
    headers = {'nuvla-authn-info': nuvla_api_authn_header}
    resp = requests.get(config_url, headers=headers)
    if resp.status_code != 200:
        raise EnvironmentError(f'Failed to get response from server: status {resp.status_code}')
    return resp.json()


def load_smtp_config_from_file() -> dict:
    if not os.path.exists(os.environ['SMTP_CONFIG']):
        raise FileNotFoundError(f"SMTP config file not found: {os.environ['SMTP_CONFIG']}")
    with open(os.environ['SMTP_CONFIG'], 'r') as f:
        return yaml.safe_load(f)


def load_smtp_params() -> SMTPParams:
    try:
        if SMTP_CONFIG_ENV in os.environ:
            config = load_smtp_config_from_file()
            log_local.info('Loaded SMTP config from file: %s', os.environ[SMTP_CONFIG_ENV])
        else:
            config = get_smtp_config_from_nuvla()
            log_local.info('Loaded SMTP config from Nuvla API: %s', NUVLA_API_LOCAL)

        provider = config.get('smtp-xoauth2')
        if provider == 'google':
            return SMTPParamsGoogle(**config)
        raise ValueError(f'Unsupported XOAUTH2 provider: {provider}')
    except Exception as ex:
        msg = (f'Failed getting XOAUTH2 config either from config or '
               f'configuration/nuvla: {ex}')
        log_local.error(msg)
        raise ValueError(msg)


KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_EMAIL_S'
KAFKA_GROUP_ID = 'nuvla-notification-email'

SEND_EMAIL_ATTEMPTS = 3


def get_smtp_client(smtp_parms: SMTPParams) -> XOAuth2SMTPClient:
    if smtp_parms is None:
        log_local.error('SMTP parameters must be provided to initialize the SMTP client.')
        raise ValueError('SMTP parameters must be provided.')
    if smtp_parms.provider() == 'google':
        smtp_client = XOAuth2SMTPClientGoogle(smtp_parms)
        log_local.info('XOAUTH2 SMTP client initialized.')
        return smtp_client
    msg = f'Unsupported XOAUTH2 provider: {smtp_parms.provider()}'
    log_local.error(msg)
    raise ValueError(msg)


def get_email_template(msg_params: dict) -> Template:
    if 'TEMPLATE' not in msg_params:
        return EMAIL_TEMPLATES['default']
    tmpl_name = msg_params.get('TEMPLATE', 'default')
    template = EMAIL_TEMPLATES.get(tmpl_name)
    if template is None:
        log_local.warning('Failed to find email template %s. Using default.',
                          tmpl_name)
        template = EMAIL_TEMPLATES['default']
    return template


def html_content(msg_params: dict):
    r_uri = msg_params.get('RESOURCE_URI')
    link_text = msg_params.get('RESOURCE_NAME') or r_uri
    component_link = f'<a href="{NUVLA_ENDPOINT}/ui/{r_uri}">{link_text}</a>'

    if msg_params.get('RECOVERY', False):
        img_alert = IMG_ALERT_OK
        notif_title = f"[OK] {msg_params.get('SUBS_NAME')}"
    else:
        img_alert = IMG_ALERT_NOK
        notif_title = f"[Alert] {msg_params.get('SUBS_NAME')}"

    subs_name = 'Notification configuration'
    subs_config_link = f'<a href="{NUVLA_ENDPOINT}/ui/notifications">{subs_name}</a>'

    params = {
        'title': notif_title,
        'subs_description': msg_params.get('SUBS_DESCRIPTION'),
        'component_link': component_link,
        'metric': msg_params.get('METRIC'),
        'timestamp': timestamp_convert(msg_params.get('TIMESTAMP')),
        'subs_config_link': subs_config_link,
        'header_img': f'{NUVLA_ENDPOINT}/{img_alert}',
        'current_year': str(datetime.now().year)
    }

    if 'TRIGGER_RESOURCE_PATH' in msg_params:
        resource_path = msg_params.get('TRIGGER_RESOURCE_PATH')
        resource_name = msg_params.get('TRIGGER_RESOURCE_NAME')
        params['trigger_link'] = \
            f'<a href="{NUVLA_ENDPOINT}/ui/{resource_path}">{resource_name}</a>'

    if msg_params.get('CONDITION'):
        params['condition'] = msg_params.get('CONDITION')
        if msg_params.get('VALUE'):
            params['condition'] = f"{msg_params.get('CONDITION')} {msg_params.get('CONDITION_VALUE')}"
            params['value'] = msg_params.get('VALUE')

    return get_email_template(msg_params).render(**params)


def send(smtp_client: XOAuth2SMTPClientGoogle, recipients, subject, html,
         attempts=SEND_EMAIL_ATTEMPTS, sleep_interval=0.5, smtp_params: SMTPParams = None):
    wname = multiprocessing.current_process().name
    for i in range(attempts):
        try:
            smtp_client.send_email(
                recipients=recipients,
                subject=subject,
                html=html
            )
            log_local.info(f'Email sent to {recipients}')
            return
        except smtplib.SMTPException as ex:
            if i < attempts - 1:  # no need to sleep on the last iteration
                time.sleep(sleep_interval)
                log_local.error(f'{wname} - Failed sending email due to SMTP error: {ex}')
                log_local.warning(f'{wname} - Reconnecting to SMTP server...')
                smtp_client.stop()
                smtp_client = get_smtp_client(smtp_params)
                log_local.warning(f'{wname} - Reconnecting to SMTP server... done.')
        except Exception as ex:
            log_local.error(f'Failed sending email: {ex}')
            NOTIFICATIONS_ERROR.labels('email', subject, ','.join(recipients), type(ex)).inc()
            PROCESS_STATES.state('error - recoverable')
            if i < attempts - 1:
                time.sleep(sleep_interval)
            smtp_client.stop()
            smtp_client = get_smtp_client(smtp_params)
    raise SendFailedMaxAttempts(f'Failed sending email after {attempts} attempts.')


def get_recipients(v: dict) -> list:
    return list(filter(lambda x: x != '', v.get('DESTINATION', '').split(' ')))


def worker(workq: multiprocessing.Queue, smtp_params: SMTPParams = None):
    wname = multiprocessing.current_process().name
    log_local.info('Worker started: %s', wname)
    smtp_client = get_smtp_client(smtp_params)
    while True:
        PROCESS_STATES.state('idle')
        msg = workq.get()
        PROCESS_STATES.state('processing')
        if msg:
            recipients = get_recipients(msg.value)
            if len(recipients) == 0:
                log_local.warning(f'{wname} - No recipients provided in: {msg.value}')
                continue
            r_id = msg.value.get('RESOURCE_ID')
            r_name = msg.value.get('NAME')
            subject = msg.value.get('SUBS_NAME') or f'{r_name or r_id} alert'
            try:
                html = html_content(msg.value)
                send(smtp_client, recipients, subject, html, smtp_params=smtp_params)
                log_local.info(f'{wname} - sent: {msg} to {recipients}')
                NOTIFICATIONS_SENT.labels('email', f'{r_name or r_id}', ','.join(recipients)).inc()
            except Exception as ex:
                # TODO: Put unsent message to error queue.
                log_local.error(f'{wname} Failed sending email: {ex}')
                NOTIFICATIONS_ERROR.labels('email', r_name, ','.join(recipients), type(ex)).inc()
                PROCESS_STATES.state('error - recoverable')


def email_template(template_file=EMAIL_TEMPLATE_DEFAULT_FILE):
    return Template(open(template_file).read())


def init_email_templates(default=EMAIL_TEMPLATE_DEFAULT_FILE,
                         app_pub=EMAIL_TEMPLATE_APP_PUB_FILE):
    EMAIL_TEMPLATES['default'] = email_template(default)
    EMAIL_TEMPLATES['app-pub'] = email_template(app_pub)


if __name__ == "__main__":
    init_email_templates()
    smtp_params = load_smtp_params()
    assert smtp_params is not None, ('SMTP parameters must be set before starting the worker.')
    start_http_server(prometheus_exporter_port(), registry=registry)
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID, initargs=(smtp_params,))
