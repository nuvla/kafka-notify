from prometheus_client import Counter, Enum

NAMESPACE = 'kafka_notify'

PROCESS_STATES = Enum('process_states', 'State of the process', states=['idle', 'processing',
                                                                                     'error - recoverable', 'error - '
                                                                                     'need restart']
                      , namespace=NAMESPACE)

NOTIFICATIONS_SENT = Counter('notifications_sent', 'Number of notifications sent',
                             ['type', 'name', 'endpoint'], namespace=NAMESPACE)
NOTIFICATIONS_ERROR = Counter('notifications_error',
                              'Number of notifications that could not be sent due to error',
                              ['type', 'name', 'endpoint', 'exception'], namespace=NAMESPACE)
