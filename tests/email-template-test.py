#!/usr/bin/env python3

import json
import os

import notify_email
notify_email.init_email_templates(
    default=os.path.join('..', 'src', notify_email.EMAIL_TEMPLATE_DEFAULT_FILE),
    app_pub=os.path.join('..', 'src', notify_email.EMAIL_TEMPLATE_APP_PUB_FILE))

tests = [
    'event-app-pub-app-bq.json',
    'event-app-pub-depl-grp.json',
    'event-app-pub-depl.json',
    'metric-no-value-NOK.json',
    'metric-no-value-OK.json',
    'metric-with-value-NOK.json',
    'metric-with-value-OK.json',
    'ne-online-true.json',
    'ne-online-false.json'
]

for t in tests:
    values = json.loads(open(t).read())
    open(t.replace('json', 'html'), 'w').write(notify_email.html_content(values))
