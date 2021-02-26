#!/usr/bin/env python3

import sys
import json
import notify_slack

# Slack webhook URL
dest = sys.argv[1]

tests = [
    'metric-no-value-NOK.json',
    'metric-no-value-OK.json',
    'metric-with-value-NOK.json',
    'metric-with-value-OK.json'
]

for t in tests:
    values = json.loads(open(t).read())
    notify_slack.send_message(dest, notify_slack.message_content(values))
