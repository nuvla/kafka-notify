#!/usr/bin/env python3

import json
from datetime import datetime
import multiprocessing
import requests
import os
import re
from paho.mqtt import client as mqtt
from paho.mqtt import publish as publish


from notify_deps import get_logger, timestamp_convert, main
from notify_deps import NUVLA_ENDPOINT, prometheus_exporter_port
from prometheus_client import start_http_server
from metrics import PROCESS_STATES, NOTIFICATIONS_SENT, NOTIFICATIONS_ERROR, registry

KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC') or 'NOTIFICATIONS_SLACK_S'
KAFKA_GROUP_ID = 'nuvla-notification-mqtt'

log_local = get_logger('mqtt-notifier')

gt = re.compile('>')
lt = re.compile('<')

COLOR_OK = "#2C9442"
COLOR_NOK = "#B70B0B"

def now_timestamp():
    return datetime.now().timestamp()

def message_content(msg_params: dict):
    log_local.info(f"Building message content for {msg_params}")

    r_uri = msg_params.get('RESOURCE_URI')
    link_text = msg_params.get('RESOURCE_NAME') or r_uri
    component_link = f'<{NUVLA_ENDPOINT}/ui/{r_uri}|{link_text}>'

    for key, value in msg_params.items():
        log_local.info(f"Key: {key}, Value: {value}")
        if value is None:
            msg_params[key] = ''

    FIELDS=["SUBS_ID",
            "NAME",
            "SUBS_NAME",
            "SUBS_DESCRIPTION",
            "RESOURCE_URI",
            "RESOURCE_NAME",
            "RESOURCE_DESCRIPTION",
            "METRIC",
            "CONDITION",
            "CONDITION_VALUE",
            "VALUE",
            "TIMESTAMP",
            "TRIGGER_RESOURCE_PATH",
            "TRIGGER_RESOURCE_NAME",
            "RECOVERY",
            ]
    
    outfield = {}
    for ffield in FIELDS:
        log_local.info(f"Field: {ffield}, Value: {msg_params.get(ffield)}")
        if msg_params.get(ffield):
            outfield[ffield] = msg_params.get(ffield)
            # outfield.append({ffield: msg_params.get(ffield),})

    # Order of the fields defines the layout of the message
    if msg_params.get('TRIGGER_RESOURCE_PATH'):
        resource_path = msg_params.get('TRIGGER_RESOURCE_PATH')
        resource_name = msg_params.get('TRIGGER_RESOURCE_NAME')
        trigger_link = \
            f'<{NUVLA_ENDPOINT}/ui/{resource_path}|{resource_name}>'
        
    outfield['COMPONENT_LINK'] = component_link
    outfield['ts'] = now_timestamp()

    return outfield

def send_mqtt_notification(payload, mqtt_server: str):
    host,port,topic = extract_destination(mqtt_server)
    if not port:
        port = 1883
    log_local.info(f"Sending message to {host}:{port}/{topic}")
    return publish.single(topic, payload, hostname=host, port=int(port))

def send_message(message, mqtt_server: str):
    return send_mqtt_notification(json.dumps(message), mqtt_server)

def extract_destination(dest: str) -> tuple:
    log_local.info(f"Extracting destination from {dest}")
    topic = dest.split('/', 1)[1]
    log_local.info(f"Extracted topic: {topic}")
    if len(dest.split(':')) == 1:
        hostname = dest.split('/', 1)[0]
        return hostname, None, topic
    hostname = dest.split(':', 1)[0]
    port = dest.split(':', 1)[1].split('/', 1)[0]
    return hostname, port, topic

def worker(workq: multiprocessing.Queue):
    while True:
        PROCESS_STATES.state('idle')
        msg = workq.get()
        PROCESS_STATES.state('processing')

        if msg:
            log_local.info(f"Received message. key:\n{msg.key}\n")
            log_local.info(f"Received message. value:\n{msg.value}\n")
            try:
                send_message(message_content(msg.value), msg.value.get('DESTINATION'))
            except requests.exceptions.RequestException as ex:
                log_local.error(f'Failed sending {msg} to {mqtt_server}: {ex}')
                PROCESS_STATES.state('error - recoverable')
                NOTIFICATIONS_ERROR.labels('mqtt', f'{msg.value.get("NAME") \
                                                      or msg.value["SUBS_NAME"]}',
                                           mqtt_topic, type(ex)).inc()
                continue
            
            log_local.info(f'sent: {msg} to {msg.value.get('DESTINATION')} \
                           on {msg.value.get('MQTT_TOPIC')}')


if __name__ == "__main__":
    start_http_server(prometheus_exporter_port(), registry=registry)
    main(worker, KAFKA_TOPIC, KAFKA_GROUP_ID)