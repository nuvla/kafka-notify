#!/usr/bin/env python3

import requests
import re

from notify_deps import *

KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_SLACK_S'
KAFKA_GROUP_ID = 'nuvla-notification-slack'

log_local = get_logger('slack')

gt = re.compile('>')
lt = re.compile('<')

COLOR_OK = "#2C9442"
COLOR_NOK = "#B70B0B"


def message_content(values: dict):
    # subs_config_id = values.get('SUBS_ID')
    subs_name = lt.sub('&lt;', gt.sub('&gt;', values.get('SUBS_NAME', '')))
    subs_config_txt = f'<{NUVLA_ENDPOINT}/ui/notifications|{subs_name}>'

    metric = values.get('METRIC')
    if values.get('VALUE'):
        cond_value = values.get('CONDITION_VALUE')
        condition = f"{values.get('CONDITION')}"
        criteria = f'_{metric}_ {gt.sub("&gt;", lt.sub("&lt;", condition))} *{cond_value}*'
        value = f"*{values.get('VALUE')}*"
    else:
        condition = values.get('CONDITION', '').upper()
        criteria = f'_{metric}_'
        value = f'*{condition}*'

    r_uri = values.get('RESOURCE_URI')
    r_name = values.get('RESOURCE_NAME')
    link_text = r_name or r_uri
    component = f'<{NUVLA_ENDPOINT}/ui/{r_uri}|{link_text}>'

    ts = timestamp_convert(values.get('TIMESTAMP'))

    if values.get('RECOVERY', False):
        color = COLOR_OK
        notif_title = "[OK] Notification"
    else:
        color = COLOR_NOK
        notif_title = "[Alert] Notification"

    return {
        "attachments": [
            {
                "color": color,
                "author_name": "Nuvla",
                "author_link": "https://sixsq.com",
                "author_icon": "https://sixsq.com/img/logo/logo_sixsq.png",
                "fields": [
                    {
                        "title": notif_title,
                        "value": subs_config_txt,
                        "short": True
                    },
                    {
                        "title": "Affected resource",
                        "value": component,
                        "short": True
                    },
                    {
                        "title": "Criteria",
                        "value": criteria,
                        "short": True
                    },
                    {
                        "title": "Value",
                        "value": value,
                        "short": True
                    },
                    {
                        "title": "Event Timestamp",
                        "value": ts,
                        "short": True
                    }
                ],
                "ts": datetime.now().timestamp()
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
