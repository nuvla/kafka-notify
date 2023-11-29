import json
import logging
import multiprocessing
import queue
import os
import sys
import time
from datetime import datetime
from kafka import KafkaConsumer


log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s')
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(log_formatter)

logger = logging.getLogger('kafka')
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


def get_logger(who):
    global stdout_handler
    log = logging.getLogger(f'send-{who}')
    log.addHandler(stdout_handler)
    log.setLevel(logging.INFO)
    return log


log = get_logger('main')

KAFKA_BOOTSTRAP_SERVERS = ['kafka:9092']
if 'KAFKA_BOOTSTRAP_SERVERS' in os.environ:
    KAFKA_BOOTSTRAP_SERVERS = os.environ['KAFKA_BOOTSTRAP_SERVERS'].split(',')

NUVLA_ENDPOINT = (os.environ.get('NUVLA_ENDPOINT') or 'https://nuvla.io').rstrip('/')

work_queue = multiprocessing.Queue()


def kafka_consumer(topic, bootstrap_servers, group_id, auto_offset_reset='latest'):
    consumer = KafkaConsumer(topic,
                             bootstrap_servers=bootstrap_servers,
                             auto_offset_reset=auto_offset_reset,
                             group_id=group_id,
                             key_deserializer=lambda x: str(x.decode()),
                             value_deserializer=lambda x: json.loads(x.decode()))
    log.info("Kafka consumer created.")
    return consumer


def timestamp_convert(ts):
    return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ'). \
        strftime('%Y-%m-%d %H:%M:%S UTC')


def main(worker, kafka_topic, group_id):
    pool = multiprocessing.Pool(5, worker, (work_queue,))
    for msg in kafka_consumer(kafka_topic, KAFKA_BOOTSTRAP_SERVERS, group_id=group_id):
        while True:
            try:
                work_queue.put(msg, timeout=.05)
                break
            except queue.Full:
                log.warning('Queue full. Sleep 1 sec.')
                time.sleep(1)
    work_queue.close()
    work_queue.join_thread()
    pool.close()
    pool.join()

