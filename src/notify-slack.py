#!/usr/bin/env python3

import json
from datetime import datetime
import multiprocessing
import requests
import os
import re

from notify_deps import get_logger, timestamp_convert, main
from notify_deps import NUVLA_ENDPOINT

KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_SLACK_S'
KAFKA_GROUP_ID = 'nuvla-notification-slack'

log_local = get_logger('slack')

gt = re.compile('>')
lt = re.compile('<')

COLOR_OK = "#2C9442"
COLOR_NOK = "#B70B0B"


def now_timestamp():
    return datetime.now().timestamp()


def message_content(msg_params: dict):
    r_uri = msg_params.get('RESOURCE_URI')
    link_text = msg_params.get('RESOURCE_NAME') or r_uri
    component_link = f'<{NUVLA_ENDPOINT}/ui/{r_uri}|{link_text}>'

    if msg_params.get('RECOVERY', False):
        color = COLOR_OK
        notif_title = f"[OK] {msg_params.get('SUBS_NAME')}"
    else:
        color = COLOR_NOK
        notif_title = f"[Alert] {msg_params.get('SUBS_NAME')}"

    subs_config_link = f'<{NUVLA_ENDPOINT}/ui/notifications|Notification configuration>'

    # Order of the fields defines the layout of the message.

    fields = [
        {
            'title': notif_title,
            'value': subs_config_link,
            'short': True
        }
    ]

    if 'TRIGGER_RESOURCE_PATH' in msg_params:
        resource_path = msg_params.get('TRIGGER_RESOURCE_PATH')
        resource_name = msg_params.get('TRIGGER_RESOURCE_NAME')
        trigger_link = \
            f'<{NUVLA_ENDPOINT}/ui/{resource_path}|{resource_name}>'
        fields.append({
            'title': 'Application was published',
            'value': trigger_link,
            'short': True
        })

    fields.append({
        'title': 'Affected resource(s)',
        'value': component_link,
        'short': True
    })

    if msg_params.get('CONDITION'):
        metric = msg_params.get('METRIC')
        if 'VALUE' in msg_params:
            cond_value = msg_params.get('CONDITION_VALUE')
            condition = f"{msg_params.get('CONDITION')}"
            criteria = f'_{metric}_ {gt.sub("&gt;", lt.sub("&lt;", condition))} *{cond_value}*'
            value = f"*{msg_params.get('VALUE')}*"
        else:
            condition = msg_params.get('CONDITION', '').upper()
            criteria = f'_{metric}_'
            value = f'*{condition}*'

        fields.extend([
            {
                'title': 'Criteria',
                'value': criteria,
                'short': True
            },
            {
                'title': 'Value',
                'value': value,
                'short': True
            }]
        )

    fields.append(
        {
            'title': 'Event Timestamp',
            'value': timestamp_convert(msg_params.get('TIMESTAMP')),
            'short': True
        }
    )

    attachments = [{
            'color': color,
            'author_name': 'Nuvla.io',
            'author_link': 'https://nuvla.io',
            'author_icon': 'https://sixsq.com/assets/img/logo-sixsq.svg',
            'fields': fields,
            'footer': 'https://sixsq.com',
            'footer_icon': 'https://sixsq.com/assets/img/logo-sixsq.svg',
            'ts': now_timestamp()
        }
    ]

    return {'attachments': attachments}


def send_message(dest, message):
    return requests.post(dest, data=json.dumps(message))


def worker(workq: multiprocessing.Queue):
    while True:
        msg = workq.get()
        if msg:
            dest = msg.value['DESTINATION']
            resp = send_message(dest, message_content(msg.value))
            if not resp.ok:
                log_local.error(f'Failed sending {msg} to {dest}: {resp.text}')
            else:
                log_local.info(f'sent: {msg} to {dest}')


if __name__ == "__main__":
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID)
