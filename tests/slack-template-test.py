#!/usr/bin/env python3

import json
import sys

import notify_slack

# Slack webhook URL
dest = sys.argv[1]

tests = [
    'event-app-pub-app-bq.json',
    'event-app-pub-depl-grp.json',
    'event-app-pub-depl.json',
    'metric-no-value-NOK.json',
    'metric-no-value-OK.json',
    'metric-with-value-NOK.json',
    'metric-with-value-OK.json',
    'ne-online-true.json',
    'ne-online-false.json',
    'notification-test.json'
]

for t in tests:
    values = json.loads(open(t).read())
    notify_slack.send_message(dest, notify_slack.message_content(values))
