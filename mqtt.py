#!/usr/bin/python3 -u

from paho.mqtt import client as mqtt_client
from config import *
from utils import *

def connect_mqtt(mqtt_client_id):

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            print("%s\tFailed to connect, return code '%d'" % (get_time(), rc))

    broker = MQTT_BROKER_HOST
    port = MQTT_BROKER_PORT

    print("%s\tInit MQTT connection to '%s:%s' as client '%s'..." % (get_time(), broker, port, mqtt_client_id))

    client = mqtt_client.Client(mqtt_client_id)
    client.username_pw_set(MQTT_BROKER_LOGIN, MQTT_BROKER_PASSWORD)
    client.on_connect = on_connect
    client.connect(broker, port)

    return client

