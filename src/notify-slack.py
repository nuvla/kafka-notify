#!/usr/bin/env python3

import requests

from notify_deps import *


KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_SLACK_S'
KAFKA_GROUP_ID = 'nuvla-notification-slack'

log_local = get_logger('slack')


def worker(workq: multiprocessing.Queue):
    while True:
        msg = workq.get()
        if msg:
            dest = msg.value['DESTINATION']
            r_id = msg.value.get('RESOURCE_ID')
            r_name = msg.value.get('NAME')
            link_text = r_name or r_id
            r_message = msg.value.get('MESSAGE')
            subs_config_id = msg.value.get('SUBS_ID')
            subs_config_txt = f'<{NUVLA_ENDPOINT}/ui/api/{subs_config_id}|Notification configuration.>'
            m = {
                "blocks": [
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "image",
                                "image_url": "https://api.slack.com/img/blocks/bkb_template_images/notificationsWarningIcon.png",
                                "alt_text": "notifications warning icon"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{NUVLA_ENDPOINT}/ui/api/{r_id}|{link_text}> *{r_message}* {subs_config_txt}"
                    }
                    }
                ]
            }
            requests.post(dest, data=json.dumps(m))
            log_local.info(f'sent: {m} to {dest}')


if __name__ == "__main__":
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID)
