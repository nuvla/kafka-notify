## Release process

The release process is automated using GitHub Actions. The release process gets
triggered when a new tag is pushed to the repository. The release process is 
defined in the `.github/workflows/release.yml` file.


## Nuvla specific scripts for notifiation of users

Kafka topics are used as the source of the messages.

Messages can be sent to Slack, Email, or MQTT broker. See examples below. Where
applicable, environment variables contain source code defaults.

```
services:

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
    command:
      - email
    environment:
      - KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
      - KAFKA_TOPIC: "NOTIFICATIONS_EMAIL_S"
      # If $SMTP_CONFIG is not provided, the configuration will be taken 
      # from configuration/nuvla resource.
      - SMTP_CONFIG: /etc/nuvla/smtp-config.yaml
      - NUVLA_ENDPOINT: https://nuvla.io
    # Set along with the SMTP_CONFIG environment variable
    config:
        - source: smtp-config
          target: /etc/nuvla/smtp-config.yaml
      
configs:
    # Set along with the SMTP_CONFIG environment variable
    smtp-config:
      file: smtp-config.yaml
```

For the example of `smtp-config.yaml`, see the [smtp-config-xoauth2-google.yaml.example](smtp-config-xoauth2-google.yaml.example) file.
