import unittest

from notify_email import get_recipients


class NotifyEmail(unittest.TestCase):

    def test_get_recipients(self):
        assert 0 == len(get_recipients({}))
        e1 = 'a@b.c'
        e2 = 'a@b.c'
        assert [e1] == get_recipients({'DESTINATION': e1})
        assert [e1, e2] == get_recipients({'DESTINATION': f'{e1} {e2}'})
        assert [e1, e2] == get_recipients({'DESTINATION': f' {e1}   {e2}   '})
