#!/usr/bin/python3 -u

import sys
import os
import time
from datetime import datetime
#from paho.mqtt import client as mqtt_client
from config import *
from mqtt import *
from utils import *
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InterruptedException


MQTT_CLIENT_ID = f"{VOROTA_NAME}_SIM800L_SERVICE"

client = None

def get_time():
        return datetime.now().strftime("%Y-%m-%d %H:%I:%S")

def publish_message(topic, message):

    global client

    result = client.publish(topic, message)
    status = result[0]

    print("%s\tPublish message '%s' to topic '%s', status=%s" % (get_time(), message, topic, "SUCCESS" if status == 0 else "ERROR_" % status))

    return result


def handle_incoming_call(call):

    if call.ringCount == 1:
        print("%s\tIncoming call from: number=%s, TON=%s, callerName=%s" % (get_time(), call.number, call.ton, call.callerName))
        publish_message(INCOMING_CALL_TOPIC_NAME, call.number)

    elif call.ringCount >= 3:
        print("%s\tHanging up call from %s." % (get_time(), call.number))
        call.hangup()

def run():

    global client

    # mqtt
    client = connect_mqtt(MQTT_CLIENT_ID)
    client.loop_start()

    # modem
    print("%s\tInit modem on port %s, baudrate=%s..." % (get_time(), MODEM_PORT, MODEM_BAUDRATE ))

    modem = GsmModem(MODEM_PORT, MODEM_BAUDRATE, incomingCallCallbackFunc=handle_incoming_call)
    modem.connect(MODEM_SIM_PIN)

    print("%s\tWaiting for incoming calls..." % get_time())

    try:
        modem.rxThread.join(2**31) # Specify a (huge) timeout so that it essentially blocks indefinitely, but still receives CTRL+C interrupt signal
    finally:
        modem.close()

def main():
    run()

main()



