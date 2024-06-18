#!/usr/bin/env bash

curl -LO https://www.emqx.com/en/downloads/MQTTX/v1.10.0/mqttx-cli-linux-arm64
sudo install ./mqttx-cli-linux-arm64 /usr/local/bin/mqttx
rm mqttx-cli-linux-arm64