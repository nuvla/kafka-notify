from prometheus_client import Counter

NAMESPACE = 'kafka_notify'

NOTIFICATIONS_SENT = Counter(f'{NAMESPACE}_notifications_sent', 'Number of notifications sent',
                             ['type', 'subscription_name', 'endpoint'])
NOTIFICATIONS_ERROR = Counter(f'{NAMESPACE}_notifications_error', 'Number of notifications that could not be sent due to error',
                              ['type', 'subscription_id', 'endpoint', 'exception'])
