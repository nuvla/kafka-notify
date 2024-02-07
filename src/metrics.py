from prometheus_client import Counter

NOTIFICATIONS_SENT = Counter('notifications_sent', 'Number of notifications sent',
                             ['type', 'subscription_name', 'endpoint'])
NOTIFICATIONS_ERROR = Counter('notifications_error', 'Number of notifications that could not be sent due to error',
                              ['type', 'subscription_id', 'endpoint', 'exception'])
