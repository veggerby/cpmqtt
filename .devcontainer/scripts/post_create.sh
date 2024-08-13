#!/usr/bin/env bash

# Bash completion

# Install tools

architecture="$(uname -m)"
case ${architecture} in
    amd64) architecture='x64' ;;
    x86_64) architecture='x64' ;;
    aarch64) architecture='arm64' ;;
    *) echo "Unsupported architecture: $architecture"; exit 1 ;;
esac

if [ -x "$(command -v pip)" ]; then
    pip install --upgrade pip && pip install -r requirements.txt
fi

check_packages() {
    if ! dpkg -s "$@" > /dev/null 2>&1; then
        sudo apt update
        sudo apt-get -y install --no-install-recommends "$@"
    fi
}

curl -L "https://www.emqx.com/en/downloads/MQTTX/v1.10.0/mqttx-cli-linux-${architecture}" -o mqttx-cli-linux
sudo install ./mqttx-cli-linux /usr/local/bin/mqttx

if [ -f mqttx-cli-linux ]; then
    rm mqttx-cli-linux
fi

check_packages bash-completion xdg-utils pass
