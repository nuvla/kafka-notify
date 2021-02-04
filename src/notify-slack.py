#!/usr/bin/env python3

import requests

from notify_deps import *

KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_SLACK_S'
KAFKA_GROUP_ID = 'nuvla-notification-slack'

log_local = get_logger('slack')


def build_text(values: dict):
    # subs_config_id = values.get('SUBS_ID')
    subs_name = values.get('SUBS_NAME')
    subs_config_txt = f'<{NUVLA_ENDPOINT}/ui/notifications|{subs_name}>'

    metric = values.get('METRIC')
    if values.get('VALUE'):
        # values.get('CONDITION_VALUE')
        condition = f"{values.get('CONDITION')}"
        value = values.get('VALUE')
        message = f'_{metric}_ *{condition}* *{value}*'
    else:
        condition = values.get('CONDITION')
        message = f'_{metric}_ *{condition}*'

    r_uri = values.get('RESOURCE_URI')
    r_name = values.get('RESOURCE_NAME')
    link_text = r_name or r_uri
    component = f'<{NUVLA_ENDPOINT}/ui/{r_uri}|{link_text}>'

    ts = timestamp_convert(values.get('TIMESTAMP'))

    msg = f":ghost:\n{subs_config_txt}\n{component}\n{message}\n{ts}"
    return msg


def message_content(values: dict):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": build_text(values)
                }
            }
        ]
    }


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
