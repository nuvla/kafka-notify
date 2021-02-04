#!/usr/bin/env python3

import json
from jinja2 import Template

import notify_email

notify_email.EMAIL_TEMPLATE = Template(open('../src/templates/base.html').read())

values = json.loads(open('metric-no-value.json').read())
open('email-no-value.html', 'w').write(notify_email.html_content(values))

values = json.loads(open('metric-with-value.json').read())
open('email-with-value.html', 'w').write(notify_email.html_content(values))
