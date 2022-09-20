import unittest

from notify_slack import now_timestamp


class NotifyEmail(unittest.TestCase):

    def test_now_timestamp(self):
        assert isinstance(now_timestamp(), float)
