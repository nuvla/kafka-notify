## Nuvla specific scripts for notifiation of users

Kafka topics are used as the source of the messages.

Messages can be sent to Slack or Email. See examples below. Where
applicable, environment variables contain source code defaults.

```
  notify-slack:
    image: nuvladev/kafka-notify:master
    networks:
      - test-net
    environment:
      - KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
      - KAFKA_TOPIC: "NOTIFICATIONS_SLACK_S"
      - NUVLA_ENDPOINT: "https://nuvla.io"
    command:
      - slack

  notify-email:
    image: nuvladev/kafka-notify:master
    networks:
      - test-net
    environment:
      - KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
      - KAFKA_TOPIC: "NOTIFICATIONS_EMAIL_S"
      - NUVLA_ENDPOINT: "https://nuvla.io"
      # If not provided, will be taken from configuration/nuvla resource.
      - SMTP_HOST: 
      - SMTP_PORT:
      - SMTP_SSL: 
      - SMTP_USER: 
      - SMTP_PASSWORD:
    command:
      - email
```