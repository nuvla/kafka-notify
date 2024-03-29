import unittest
import os
from unittest.mock import Mock
import shutil
from prometheus_client import multiprocess

os.environ['PROMETHEUS_MULTIPROC_DIR'] = ''
os.path.exists = Mock(return_value=True)
os.mkdir = Mock()
shutil.rmtree = Mock()

multiprocess.MultiProcessCollector = Mock()

from notify_slack import now_timestamp, message_content


class NotifyEmail(unittest.TestCase):

    @staticmethod
    def test_now_timestamp():
        assert isinstance(now_timestamp(), float)

    @staticmethod
    def test_message_content_condition_optional():
        msg = {'CONDITION': 'foo',
               'TIMESTAMP': '2023-11-09T10:29:31Z'}
        fields = message_content(msg)['attachments'][0]['fields']
        assert 2 == len(list(filter(
            lambda x: x['title'] in ['Criteria', 'Value'], fields)))

        msg = {'TIMESTAMP': '2023-11-09T10:29:31Z'}
        fields = message_content(msg)['attachments'][0]['fields']
        assert 0 == len(list(filter(
            lambda x: x['title'] in ['Criteria', 'Value'], fields)))
