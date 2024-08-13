#!/bin/bash

# Define the MQTT broker, topic, and other parameters
BROKER="192.168.1.156"
USER="admin"
PASSWORD="password"
TOPIC="test/topic"
CLIENT_PREFIX="cli"

# Subscribe to the same topic 10 times in parallel
for i in {1..10}
do
    CLIENT_ID="${CLIENT_PREFIX}_${i}"

    # mqttx sub -t ping -q 1 -V 3.1.1 -h 192.168.1.156 -u admin -P password -i test

    mqttx sub \
        -h ${BROKER} \
        -t ${TOPIC} \
        -i ${CLIENT_ID} \
        -q 1 \
        -V 3.1.1 \
        -u ${USER} \
        -P ${PASSWORD} \
        &

done

# Wait for all background processes to finish
wait
