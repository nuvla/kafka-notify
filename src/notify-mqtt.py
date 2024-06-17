#!/usr/bin/env python3

import multiprocessing
import os
import threading
from urllib.parse import urlparse

from paho.mqtt import publish as mqtt_publish
from prometheus_client import start_http_server

from notify_deps import get_logger, main
from notify_deps import NUVLA_ENDPOINT, prometheus_exporter_port
from metrics import PROCESS_STATES, NOTIFICATIONS_SENT, NOTIFICATIONS_ERROR, registry

KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_MQTT_S'
KAFKA_GROUP_ID = 'nuvla-notification-mqtt'

log_local = get_logger('mqtt-notifier')


def message_content(msg_params: dict) -> dict:
    log_local.debug('Building message content for: %s', msg_params)

    r_uri = msg_params.get('RESOURCE_URI')
    link_text = msg_params.get('RESOURCE_NAME') or r_uri
    component_link = f'<{NUVLA_ENDPOINT}/ui/{r_uri}|{link_text}>'

    for key, value in msg_params.items():
        if value is None:
            msg_params[key] = ''

    attrs = [
        'SUBS_ID',
        'NAME',
        'SUBS_NAME',
        'SUBS_DESCRIPTION',
        'RESOURCE_URI',
        'RESOURCE_NAME',
        'RESOURCE_DESCRIPTION',
        'METRIC',
        'CONDITION',
        'CONDITION_VALUE',
        'VALUE',
        'TIMESTAMP',
        'TRIGGER_RESOURCE_PATH',
        'TRIGGER_RESOURCE_NAME',
        'RECOVERY']

    result = {}
    for attr in attrs:
        if msg_params.get(attr):
            result[attr] = msg_params.get(attr)

    # Order of the fields defines the layout of the message
    if msg_params.get('TRIGGER_RESOURCE_PATH'):
        resource_path = msg_params.get('TRIGGER_RESOURCE_PATH')
        resource_name = msg_params.get('TRIGGER_RESOURCE_NAME')
        trigger_link = \
            f'<{NUVLA_ENDPOINT}/ui/{resource_path}|{resource_name}>'
        result['TRIGGER_LINK'] = trigger_link

    result['COMPONENT_LINK'] = component_link

    return result


def extract_destination(dest: str) -> tuple:
    # Prepend a dummy scheme for a proper parsing
    parsed_url = urlparse('//' + dest)

    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 1883
    uri = parsed_url.path.lstrip('/')

    return host, port, uri


def send_mqtt_notification(payload, mqtt_server: str):
    host, port, topic = extract_destination(mqtt_server)
    log_local.info(f'Sending message to {host}:{port}/{topic}')
    return mqtt_publish.single(topic, payload, hostname=host, port=int(port))


def send_message(payload, mqtt_server):
    def thread_function():
        try:
            send_mqtt_notification(payload, mqtt_server)
        except Exception as e:
            log_local.error(f'An error occurred: {e}')

    thread = threading.Thread(target=thread_function)
    thread.start()


def worker(workq: multiprocessing.Queue):
    while True:
        PROCESS_STATES.state('idle')

        msg = workq.get()
        if not msg:
            continue

        PROCESS_STATES.state('processing')

        log_local.debug("Received message. Key: %s. Value: %s", msg.key, msg.value)
        subs_name = msg.value.get('NAME') or msg.value['SUBS_NAME']
        dest = msg.value['DESTINATION']
        try:
            send_message(message_content(msg.value), dest)
        except Exception as ex:
            err_msg = f'Failed sending message: {subs_name} to {dest}'
            log_local.error(err_msg)
            PROCESS_STATES.state('error - recoverable')
            NOTIFICATIONS_ERROR.labels('mqtt', subs_name, dest, type(ex)).inc()
            continue

        NOTIFICATIONS_SENT.labels('mqtt', subs_name, dest).inc()
        log_local.info(f'sent: {msg} to {dest}')


if __name__ == "__main__":
    start_http_server(prometheus_exporter_port(), registry=registry)
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID)
