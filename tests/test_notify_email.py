import os
import unittest

import notify_email
from notify_email import get_recipients, html_content, email_template, EMAIL_TEMPLATE_FILE

notify_email.EMAIL_TEMPLATE = email_template(
    os.path.join('..', 'src', EMAIL_TEMPLATE_FILE))


class NotifyEmail(unittest.TestCase):

    def test_get_recipients(self):
        assert 0 == len(get_recipients({}))
        e1 = 'a@b.c'
        e2 = 'a@b.c'
        assert [e1] == get_recipients({'DESTINATION': e1})
        assert [e1, e2] == get_recipients({'DESTINATION': f'{e1} {e2}'})
        assert [e1, e2] == get_recipients({'DESTINATION': f' {e1}   {e2}   '})

    def test_html_content(self):
        msg = {'TIMESTAMP': '2023-11-09T10:29:31Z'}
        html = html_content(msg)
        assert 'Condition' not in html
        assert 'Value' not in html

        msg = {'CONDITION': 'foo',
               'VALUE': '123',
               'TIMESTAMP': '2023-11-09T10:29:31Z'}
        html = html_content(msg)
        assert 'Condition' in html
        assert 'Value' in html
