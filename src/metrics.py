import os
import shutil
from prometheus_client import multiprocess, CollectorRegistry
from prometheus_client import Counter, Enum

registry = CollectorRegistry()

path = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
if path:
    multiprocess.MultiProcessCollector(registry, path=path)
    if os.path.exists(path):
        shutil.rmtree(path)
        os.mkdir(path)

PROCESS_STATES = Enum('process_states',
                      'State of the process',
                      states=['idle', 'processing', 'error - recoverable', 'error - need restart'],
                      namespace='kafka_notify', registry=registry)

NOTIFICATIONS_SENT = Counter('notifications_sent',
                             'Number of notifications sent',
                             ['type', 'name', 'endpoint'],
                             namespace='kafka_notify', registry=registry)
NOTIFICATIONS_ERROR = Counter('notifications_error',
                              'Number of notifications that could not be sent due to error',
                              ['type', 'name', 'endpoint', 'exception'],
                              namespace='kafka_notify', registry=registry)
