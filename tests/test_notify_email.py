import os
import unittest
from unittest.mock import Mock
import shutil
from prometheus_client import multiprocess

import xoauth2_client


os.environ['PROMETHEUS_MULTIPROC_DIR'] = ''
os.path.exists = Mock(return_value=True)
os.mkdir = Mock()
shutil.rmtree = Mock()

multiprocess.MultiProcessCollector = Mock()
import notify_email
from notify_email import get_recipients, html_content, email_template

notify_email.EMAIL_TEMPLATES['default'] = email_template(
    os.path.join('src', notify_email.EMAIL_TEMPLATE_DEFAULT_FILE))

notify_email.EMAIL_TEMPLATES['app-pub'] = email_template(
    os.path.join('src', notify_email.EMAIL_TEMPLATE_APP_PUB_FILE))


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

    def test_AppAppBqPublishedDeploymentGroupUpdateNotification(self):

        affected_dpl_grp = 'affected deployment group name'
        msg = {
            'TEMPLATE': 'app-pub',

            'SUBS_ID': 'subscription-config/891bdb6c-fb8c-41e6-9023-e317757365ab',
            'SUBS_NAME': 'Apps Published for Deployment',
            'SUBS_DESCRIPTION': 'Apps Published for Deployment',

            'TRIGGER_RESOURCE_PATH': 'apps/test/new-application',
            'TRIGGER_RESOURCE_NAME': 'test',

            'RESOURCE_URI': 'deployment-groups/8c9cf316-6092-4d98-97e6-bbf030c1a1ce?deployment-groups-detail-tab=apps',
            'RESOURCE_NAME': f'Update Deployment Group: {affected_dpl_grp}',

            'TIMESTAMP': '2023-11-29T13:22:26Z',
            'RECOVERY': True
        }
        html = html_content(msg)
        open('email-Apps-Published-for-Deployment.html', 'w').write(html)

    def test_AppPublishedAppsBouquetUpdateNotification(self):

        affected_app_name = 'affected app name'
        trigger_app_name = 'trigger app name'
        msg = {
            'TEMPLATE': 'app-pub',

            'SUBS_ID': 'subscription-config/891bdb6c-fb8c-41e6-9023-e317757365ab',
            'DESTINATION': 'https://hooks.slack.com/services/foo',

            'SUBS_NAME': 'Apps Published for App Bouquet',
            'SUBS_DESCRIPTION': 'Apps Published for App Bouquet',

            'TRIGGER_RESOURCE_PATH': 'apps/test/trigger-app-name',
            'TRIGGER_RESOURCE_NAME': trigger_app_name,

            'RESOURCE_URI': 'my-app-bqs/new-app-bq',
            'RESOURCE_NAME': f'Update App Bouquet: {affected_app_name}',

            'TIMESTAMP': '2023-11-29T13:22:26Z',
            'RECOVERY': True
        }
        html = html_content(msg)
        open('email-Apps-Published-for-AppBq.html', 'w').write(html)


_get_smtp_config_from_nuvla = notify_email.get_smtp_config_from_nuvla

SMTP_CONFIG_NUVLA = {
    "id": "configuration/nuvla",
    "resource-type": "configuration",
    "smtp-ssl": True,
    "smtp-port": 123,
    "smtp-host": "smtp.gmail.com",
    "smtp-username": "mailer@sixsq.com",
    "smtp-password": "",
    "smtp-debug": True,
    "smtp-xoauth2": "google",
    "smtp-xoauth2-config": {
        "client-id": "client-id",
        "client-secret": "client-secret",
        "refresh-token": "refresh-token"
    }
}


def _load_smtp_params() -> xoauth2_client.SMTPParams:
    notify_email.get_smtp_config_from_nuvla = Mock(return_value=SMTP_CONFIG_NUVLA)
    return notify_email.load_smtp_params()


class TestSMTPParams(unittest.TestCase):

    fn = 'test_smtp_config.yaml'

    def setUp(self):
        notify_email.SMTP_PARAMS = None

    def tearDown(self):
        notify_email.get_smtp_config_from_nuvla = _get_smtp_config_from_nuvla

        if notify_email.SMTP_CONFIG_ENV in os.environ:
            del os.environ[notify_email.SMTP_CONFIG_ENV]
        try:
            os.remove(self.fn)
        except:
            pass

    def test_set_smtp_params_from_nuvla_config(self):
        smtp_params = _load_smtp_params()
        self.assertEqual(smtp_params.smtp_port, 123)
        self.assertEqual(smtp_params.smtp_xoauth2, "google")
        self.assertEqual(smtp_params.provider(), "google")
        self.assertEqual(smtp_params.smtp_xoauth2_config.client_id, "client-id")

    def test_load_from_file(self):
        os.environ[notify_email.SMTP_CONFIG_ENV] = self.fn
        with open(self.fn, 'w') as f:
            f.write("""smtp-port: 587
smtp-host: smtp.gmail.com
smtp-username: user@example.com
smtp-debug: true
smtp-xoauth2: google
smtp-xoauth2-config:
  client-id: client-id
  client-secret: client-secret
  refresh-token: refresh-token
""")

        config = notify_email.load_smtp_config_from_file()

        assert config['smtp-port'] == 587
        assert config['smtp-host'] == 'smtp.gmail.com'
        assert config['smtp-xoauth2-config']['client-id'] == 'client-id'

    def test_load_from_file_missing(self):
        os.environ[notify_email.SMTP_CONFIG_ENV] = self.fn
        with self.assertRaises(FileNotFoundError):
            notify_email.load_smtp_config_from_file()


class TestSMTPClient(unittest.TestCase):

    def setUp(self):
        notify_email.SMTP_PARAMS = None
        xoauth2_client.XOAuth2SMTPClientGoogle._refresh_token_now = Mock()

    def tearDown(self):
        notify_email.get_smtp_config_from_nuvla = _get_smtp_config_from_nuvla

    def test_get_smtp_client(self):
        smtp_params = _load_smtp_params()
        client = notify_email.get_smtp_client(smtp_params)
        assert client is not None
        assert hasattr(client, 'send_email')
        assert hasattr(client, 'stop')
        assert client.smtp_host == 'smtp.gmail.com'
        assert client.smtp_port == 123
        assert client.refresh_token == 'refresh-token'
