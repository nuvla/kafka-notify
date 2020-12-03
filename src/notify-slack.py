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
            r_id = msg.value['RESOURCE_ID']
            r_state = msg.value['RESOURCE_STATE']
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
                            "text": f"<{NUVLA_ENDPOINT}/ui/api/{r_id}|{r_id}> in state *{r_state}*"
                    }
                    }
                ]
            }
            requests.post(dest, data=json.dumps(m))
            log_local.info(f'sent: {m} to {dest}')


if __name__ == "__main__":
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID)
