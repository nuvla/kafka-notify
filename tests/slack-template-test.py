#!/usr/bin/env python3

import sys
import json
import notify_slack

# Slack webhook URL
dest = sys.argv[1]

values = json.loads(open('metric-no-value.json').read())
notify_slack.send_message(dest, notify_slack.message_content(values))

values = json.loads(open('metric-with-value.json').read())
notify_slack.send_message(dest, notify_slack.message_content(values))
