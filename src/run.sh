#!/bin/sh

senders="<slack|email|mqtt>"

SENDER=${1:?"Sender ${senders} must be provided."}

if [ "${SENDER}" == "email" ]
then
  ./notify-email.py
elif [ "${SENDER}" == "slack" ]
then
  ./notify-slack.py
elif [ "${SENDER}" == "mqtt" ]
then
  ./notify-mqtt.py
else
  echo "Sender can be one of ${senders}."
  exit 1
fi
