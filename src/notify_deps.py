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
    '%(asctime)s - %(name)s - %(process)d - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
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

DEFAULT_PROMETHEUS_EXPORTER_PORT = 9140


def kafka_consumer(topic, bootstrap_servers, group_id, auto_offset_reset='latest'):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset=auto_offset_reset,
        group_id=group_id,
        key_deserializer=lambda x: '' if x is None else str(x.decode()),
        value_deserializer=lambda x: {} if x is None else json.loads(x.decode()))
    log.info("Kafka consumer created.")
    return consumer


def timestamp_convert(ts):
    return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ'). \
        strftime('%Y-%m-%d %H:%M:%S UTC')


def now_timestamp():
    return datetime.now().timestamp()


def prometheus_exporter_port():
    return int(os.environ.get('PROMETHEUS_EXPORTER_PORT', DEFAULT_PROMETHEUS_EXPORTER_PORT))


def main(worker_fn, kafka_topic: str, group_id: str, *, initargs: tuple = (),
         num_workers: int = 5, queue_maxsize: int = 100,
         consumer_poll_timeout: float = 0.05):
    """
    Launch a pool of worker processes consuming Kafka messages.

    Parameters:
        worker_fn: Worker function run in each process.
        kafka_topic: Kafka topic to consume from.
        group_id: Kafka consumer group ID.
        initargs: Tuple of arguments passed to each worker process.
        num_workers: Number of worker processes.
        queue_maxsize: Max size of shared work queue.
        consumer_poll_timeout: Timeout for placing item in queue.
    """

    log.info("Starting Kafka worker pool with topic '%s' and group '%s'", kafka_topic, group_id)

    work_queue = multiprocessing.Queue(maxsize=queue_maxsize)

    # Extend initargs to include the work_queue
    extended_initargs = (work_queue,) + initargs

    # Create worker pool
    pool = multiprocessing.Pool(
        processes=num_workers,
        initializer=worker_fn,
        initargs=extended_initargs
    )

    try:
        consumer = kafka_consumer(kafka_topic, KAFKA_BOOTSTRAP_SERVERS, group_id=group_id)
        for msg in consumer:
            while True:
                try:
                    work_queue.put(msg, timeout=consumer_poll_timeout)
                    break
                except queue.Full:
                    log.warning('Work queue full. Sleeping 1 second before retrying...')
                    time.sleep(1)
    except KeyboardInterrupt:
        log.warning("Interrupted by user. Shutting down.")
    except Exception as e:
        log.error("Unhandled error in main loop: %s", e)
    finally:
        work_queue.close()
        work_queue.join_thread()
        pool.close()
        pool.join()
        log.info("Kafka worker pool shut down gracefully.")