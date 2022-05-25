#!/bin/bash

. ./config

install() {

    SERVICE_NAME=${1:-}
    SERVICE_FILENAME=${SERVICE_NAME}.service
    SERVICE_TEMPLATE_FILE=${SERVICE_FILENAME}.template

    envsubst < "$SERVICE_TEMPLATE_FILE" > "$SERVICE_FILENAME"

    if [ -f "$SERVICE_FILENAME" ]; then

	sudo ln -s "$(realpath "$SERVICE_FILENAME")" /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable "$SERVICE_NAME"
	sudo systemctl start "$SERVICE_NAME"
    fi
}

install "$SERVICE_NAME"
systemctl status "$SERVICE_NAME"

