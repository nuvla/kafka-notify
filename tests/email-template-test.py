#!/usr/bin/env python3

import json
from jinja2 import Template

import notify_email

notify_email.EMAIL_TEMPLATE = Template(open('../src/templates/base.html').read())

values = json.loads(open('metric-no-value-OK.json').read())
open('email-no-value-OK.html', 'w').write(notify_email.html_content(values))

values = json.loads(open('metric-no-value-NOK.json').read())
open('email-no-value-NOK.html', 'w').write(notify_email.html_content(values))

values = json.loads(open('metric-with-value.json').read())
open('email-with-value.html', 'w').write(notify_email.html_content(values))
