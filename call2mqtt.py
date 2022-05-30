#!/usr/bin/env python3 -u

import sys
import os
import re
import time
import traceback
import logging
import json
from datetime import datetime
from config import *
from paho.mqtt import client as mqtt_client
from utils import *
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InterruptedException
from traceback import print_exc


class Call2MQTT():

    def __init__(self, mqtt_client_id, log_level = logging.INFO):

        self.modem = None
        self.modem_restart_count = 0
        self.mqtt_client_id = mqtt_client_id

        logging.basicConfig(format='%(asctime)s\t%(levelname)s: %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M:%S')

        self.log = logging.getLogger(__class__.__name__)

        self.mqtt_client = self.connect_mqtt(self.mqtt_client_id)
        self.mqtt_client.loop_start()

        self.publish_message(START_TOPIC_NAME, get_time())

        return None


    def connect_mqtt(self, mqtt_client_id):

        def on_connect(client, userdata, flags, rc):
            if rc != 0:
                self.log.info("Failed to connect, return code '%d'" % ( rc ))

        broker = MQTT_BROKER_HOST
        port = MQTT_BROKER_PORT

        self.log.info("Init MQTT connection to '{0}:{1}' as client '{2}'...".format( broker, port, mqtt_client_id ))

        client = mqtt_client.Client(mqtt_client_id)
        client.username_pw_set(MQTT_BROKER_LOGIN, MQTT_BROKER_PASSWORD)
        client.on_connect = on_connect
        client.connect(broker, port)

        return client


    def publish_message(self, topic, message):

        result = self.mqtt_client.publish(topic, message)
        status = result[0]

        try:
            self.log.info("Publish message '{0}' to topic '{1}', result={2}, status={3}".format( str(message), topic, str(result), ("SUCCESS" if status == 0 else "ERROR_" % status) ))
        except:
            pass

        return result

    def handle_incoming_sms(self, sms):
        self.log.info(u'== SMS message received ==\nFrom: {0}\nTime: {1}\nMessage:\n{2}\n'.format(sms.number, sms.time, sms.text))
        self.publish_message(INCOMING_SMS_TOPIC_NAME, json.dumps({ 'number': sms.number, 'time' : sms.time, 'text' : sms.text }))


    def build_intl_phone_number(self, number, ton):

        ret = number
        m = re.match(r'^0(\d{3,3})(\d{6,6})$', str(number))

        if str(ton) == "161" and m:
            ret = "996" + m.group(1) + m.group(2)

        return ret


    def handle_incoming_call(self, call):

        if call.ringCount == 1:
            self.log.info("Incoming call from: number={0}, type={1}".format( call.number, call.ton ))
            json_call = {}
            intl_phone_number = build_intl_phone_number( call.number, call.ton )
            self.publish_message(INCOMING_CALL_TOPIC_NAME, json.dumps({ 'number_orig': call.number, 'type': call.ton, 'phone_number' : intl_phone_number }))

        call.hangup()


    def wait_command(self, modem_timeout_sec = 60):

        self.modem_restart_count+=1

        try:

            self.log.info("Init modem on port {0}, baudrate={1}...".format( MODEM_PORT, MODEM_BAUDRATE ))

#            modem = GsmModem(MODEM_PORT, MODEM_BAUDRATE, incomingCallCallbackFunc=self.handle_incoming_call, smsReceivedCallbackFunc=self.handle_incoming_sms)
            modem = GsmModem(MODEM_PORT, MODEM_BAUDRATE, incomingCallCallbackFunc=self.handle_incoming_call)
            modem.smsTextMode = False
            modem.connect(MODEM_SIM_PIN)

            self.modem = modem

            self.log.info("Waiting for incoming calls ({0})...".format( modem_timeout_sec ))

            modem.rxThread.join(modem_timeout_sec) # Specify a (huge) timeout so that it essentially blocks indefinitely, but still receives CTRL+C interrupt signal

            self.log.info("Restart by timeout...")

            self.modem_restart_count+=1
            self.publish_message(RESTART_TOPIC_NAME, self.modem_restart_count )

        except Exception as e:

            error_msg = repr(e)

            self.log.warning("Got error '{0}'".format( error_msg ))
            self.publish_message(ERROR_TOPIC_NAME, error_msg)

        finally:
            modem.close()




def main():

    worker = Call2MQTT(MQTT_CLIENT_ID, log_level = logging.DEBUG if DEBUG else logging.INFO);
    while(True):
        worker.wait_command(MODEM_RESTART_TIMEOUT_SEC);

main()


