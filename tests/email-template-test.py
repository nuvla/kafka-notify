#!/usr/bin/env python3

from jinja2 import Template

import notify_email

notify_email.EMAIL_TEMPLATE = Template(open('../src/templates/base.html').read())

values = {
    'SUBS_ID': 'subscription-config/1-2-3-4-5',
    'SUBS_NAME': 'NB London off-line',
    'SUBS_DESCRIPTION': 'NB in London off-line',
    'RESOURCE_URI': 'edge/1-2-3-4-5',
    'RESOURCE_NAME': 'NB London',
    'METRIC': 'NB online',
    'CONDITION': 'NO',
    'TIMESTAMP': '2021-02-01T10:11:12Z'
}
open('email-no-value.html', 'w').write(notify_email.html_content(values))

values = {
    'SUBS_ID': 'subscription-config/1-2-3-4-5',
    'SUBS_NAME': 'NB Paris CPU load high',
    'SUBS_DESCRIPTION': 'CPU load too high on NB Paris',
    'RESOURCE_URI': 'edge/1-2-3-4-5',
    'RESOURCE_NAME': 'NB Paris',
    'METRIC': 'CPU load %',
    'CONDITION': '>',
    'CONDITION_VALUE': '75',
    'VALUE': '85',
    'TIMESTAMP': '2021-02-01T10:11:12Z'
}
open('email-with-value.html', 'w').write(notify_email.html_content(values))
