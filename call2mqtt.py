#!/usr/bin/python3 -u

import sys
import os
import time
import traceback
import logging
import json
from datetime import datetime
from config import *
from mqtt import *
from utils import *
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InterruptedException
from traceback import print_exc

class Call2MQTT():

    def __init__(self, mqtt_client_id, log_level = logging.INFO):

        self.modem_restart_count = 0
        self.mqtt_client_id = mqtt_client_id

        self.mqtt_client = connect_mqtt(self.mqtt_client_id)
        self.mqtt_client.loop_start()

        self.publish_message(START_TOPIC_NAME, get_time())

        logging.basicConfig(format='%(asctime)s\t%(levelname)s: %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger('call2mqtt')

        return None


    def publish_message(self, topic, message):

        result = self.mqtt_client.publish(topic, message)
        status = result[0]

#        print("TOPIC: %s" % topic)
#        print("MESSAGE: %s" % message)
#        print("RESULT: %s" % result)

        try:
            self.log.info("Publish message '{0}' to topic '{1}', result={2}, status={3}".format( str(message), topic, str(result), ("SUCCESS" if status == 0 else "ERROR_" % status) ))
        except:
            pass

        return result


    def handle_incoming_call(self, call):

        if call.ringCount == 1:
            self.log.info("Incoming call from: number={0}, type={1}".format( call.number, call.ton ))
            self.publish_message(INCOMING_CALL_TOPIC_NAME, call.number)
            call.hangup()
        else:
            call.hangup()

#        if call.dtmfSupport:
#            print("{0}\tAnswering call and playing some DTMF tones...".format( get_time() ))
#            call.answer()
#            # Wait for a bit - some older modems struggle to send DTMF tone immediately after answering a call
#            time.sleep(2.0)
#            try:
#                call.sendDtmfTone('9515999955951')
#            except InterruptedException as e:
#                # Call was ended during playback
#                print('{0}\tDTMF playback interrupted: {1} ({2} Error {3})'.format(get_time(), e, e.cause.type, e.cause.code))
#            finally:
#                if call.answered:
##                    print("{0}\tHanging up call.".format( get_time() ))
#                    call.hangup()
#        else:
#            print("{0}\tModem has no DTMF support - hanging up call." .format( get_time() ))
#            call.hangup()

#    elif call.ringCount >= 3:
#        print("%s\tHanging up call from %s." % (get_time(), call.number))
#        call.hangup()


    def wait_incoming_call(self, modem_timeout_sec = 60):

        self.modem_restart_count+=1

        try:

            self.log.info("Init modem on port {0}, baudrate={1}...".format( MODEM_PORT, MODEM_BAUDRATE ))

            modem = GsmModem(MODEM_PORT, MODEM_BAUDRATE, incomingCallCallbackFunc=self.handle_incoming_call)
            modem.connect(MODEM_SIM_PIN)

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

    worker = Call2MQTT(MQTT_CLIENT_ID, log_level = logging.DEBUG);
    modem_timeout_sec = 30;

    while(True):
        worker.wait_incoming_call(modem_timeout_sec);

main()
