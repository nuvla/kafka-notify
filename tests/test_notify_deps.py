import unittest

from notify_deps import timestamp_convert


class NotifyDeps(unittest.TestCase):

    @staticmethod
    def test_now_timestamp():
        assert '2023-10-08 01:02:03 UTC' == timestamp_convert('2023-10-08T01:02:03Z')
