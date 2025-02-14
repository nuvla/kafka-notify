## Release process

The release process is automated using GitHub Actions. The release process gets
triggered when a new tag is pushed to the repository. The release process is 
defined in the `.github/workflows/release.yml` file.


## Nuvla specific scripts for notifiation of users

Kafka topics are used as the source of the messages.

Messages can be sent to Slack, Email, or MQTT broker. See examples below. Where
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
