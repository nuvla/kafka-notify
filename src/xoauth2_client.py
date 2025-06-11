#!/usr/bin/env python3

import base64
import smtplib
import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from pydantic import BaseModel, Field

from notify_deps import get_logger


log_local = get_logger('xoauth2-client')


class SMTPParams(BaseModel):
    smtp_port: int = Field(default=465, alias="smtp-port")
    smtp_host: str = Field(alias="smtp-host")
    smtp_username: str = Field(default=None, alias="smtp-username")
    smtp_debug: bool = Field(default=False, alias="smtp-debug")
    smtp_xoauth2: str = Field(alias="smtp-xoauth2")
    smtp_xoauth2_config: dict = Field(default_factory=dict, alias="smtp-xoauth2-config")

    def provider(self):
        return self.smtp_xoauth2


class XOAuth2ConfigGoogle(BaseModel):
    client_id: str = Field(alias="client-id")
    client_secret: str = Field(alias="client-secret")
    refresh_token: str = Field(alias="refresh-token")


class SMTPParamsGoogle(SMTPParams):
    smtp_xoauth2_config: XOAuth2ConfigGoogle = Field(
        default_factory=XOAuth2ConfigGoogle,
        alias="smtp-xoauth2-config")


class XOAuth2SMTPClient(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def send_email(self, to_emails: list, subject, html: str, from_email=None):
        pass

    @abstractmethod
    def stop(self):
        pass


class XOAuth2SMTPClientGoogle(XOAuth2SMTPClient):

    REFRESH_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"

    def __init__(self, config: SMTPParams):
        self.smtp_host = config.smtp_host
        self.smtp_port = config.smtp_port
        self.email = config.smtp_username
        self.debug_level = config.smtp_debug

        # For token retrieval
        self.client_id = config.smtp_xoauth2_config.client_id
        self.client_secret = config.smtp_xoauth2_config.client_secret
        self.refresh_token = config.smtp_xoauth2_config.refresh_token

        self._access_token = None

        self._refresh_thread = None
        self._lock = threading.Lock()
        self._stop_refresh = threading.Event()

        self._refresh_token_now()

    def _refresh_token_now(self):
        def _format_delta_time(in_seconds):
            return (datetime.now() + timedelta(seconds=in_seconds)).strftime(
                "%Y-%m-%d %H:%M:%S")
        log_local.info('Refreshing OAuth2 token...')
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        resp = requests.post(self.REFRESH_TOKEN_URL, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        with self._lock:
            self._access_token = token_data['access_token']
            expires_in = int(token_data['expires_in'])
        log_local.info(f'New access token obtained, expires in '
                       f'{expires_in} seconds at {_format_delta_time(expires_in)}.')
        # Schedule next refresh (30s before expiry, minimum 5s)
        next_refresh = max(expires_in - 30, 5)
        log_local.info(f'Scheduling next token refresh in {next_refresh} seconds at '
                       f'{_format_delta_time(next_refresh)}.')
        if not self._stop_refresh.is_set():
            self._refresh_thread = threading.Timer(next_refresh, self._refresh_token_now)
            self._refresh_thread.daemon = True
            self._refresh_thread.start()

    def _xoauth2_string(self):
        with self._lock:
            token = self._access_token
        auth_string = f"user={self.email}\1auth=Bearer {token}\1\1"
        return base64.b64encode(auth_string.encode()).decode()

    def send_email(self, recipients: list, subject, html: str, from_email=None):
        # Build message
        if from_email is None:
            from_email = self.email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'Nuvla <{from_email}>'
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        # Connect, authenticate, and send the email
        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
            server.ehlo()
            auth_string = self._xoauth2_string()
            code, response = server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
            if code != 235:
                raise Exception(f"XOAUTH2 authentication failed: {response}")
            server.sendmail(from_email, recipients, msg.as_string())

    def stop(self):
        self._stop_refresh.set()
        if self._refresh_thread:
            self._refresh_thread.cancel()
