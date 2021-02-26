#!/usr/bin/env python3

import json
from jinja2 import Template

import notify_email

notify_email.EMAIL_TEMPLATE = Template(open('../src/templates/base.html').read())

tests = [
    'metric-no-value-NOK.json',
    'metric-no-value-OK.json',
    'metric-with-value-NOK.json',
    'metric-with-value-OK.json'
]

for t in tests:
    values = json.loads(open(t).read())
    open(t.replace('json', 'html'), 'w').write(notify_email.html_content(values))
