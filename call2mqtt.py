#!/usr/bin/python3 -u

import sys
import os
import time
import traceback
from datetime import datetime
#from paho.mqtt import client as mqtt_client
from config import *
from mqtt import *
from utils import *
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InterruptedException
from traceback import print_exc


MQTT_CLIENT_ID = f"{VOROTA_NAME}_SIM800L_SERVICE"

client = None

def get_time():
        return datetime.now().strftime("%Y-%m-%d %H:%I:%S")

def publish_message(topic, message):

    global client

    result = client.publish(topic, message)
    status = result[0]

    print("TOPIC: %s" % topic)
    print("MESSAGE: %s" % message)
    print("RESULT: %s" % result)

    try:
        print("{0}\tPublish message '{1}' to topic '{2}', result={3}, status={4}".format( get_time(), str(message), topic, str(result), ("SUCCESS" if status == 0 else "ERROR_" % status) ))
    except:
        pass

    return result


def handle_incoming_call(call):

    if call.ringCount == 1:
        print("{0}\tIncoming call from: number={1}, type={2}".format( get_time(), call.number, call.ton ))
        publish_message(INCOMING_CALL_TOPIC_NAME, call.number)

    elif call.ringCount >= 2:
        if call.dtmfSupport:
            print("{0}\tAnswering call and playing some DTMF tones...".format( get_time() ))
            call.answer()
            # Wait for a bit - some older modems struggle to send DTMF tone immediately after answering a call
            time.sleep(2.0)
            try:
                call.sendDtmfTone('9515999955951')
            except InterruptedException as e:
                # Call was ended during playback
                print('{0}\tDTMF playback interrupted: {1} ({2} Error {3})'.format(get_time(), e, e.cause.type, e.cause.code))
            finally:
                if call.answered:
                    print("{0}\tHanging up call.".format( get_time() ))
                    call.hangup()
        else:
            print("{0}\tModem has no DTMF support - hanging up call." .format( get_time() ))
            call.hangup()

#    elif call.ringCount >= 3:
#        print("%s\tHanging up call from %s." % (get_time(), call.number))
#        call.hangup()

def run():

    global client

    # mqtt
    client = connect_mqtt(MQTT_CLIENT_ID)
    client.loop_start()

    try:
        print("{0}\tInit modem on port {1}, baudrate={2}...".format( get_time(), MODEM_PORT, MODEM_BAUDRATE ))

        modem = GsmModem(MODEM_PORT, MODEM_BAUDRATE, incomingCallCallbackFunc=handle_incoming_call)
        modem.connect(MODEM_SIM_PIN)

        print("{0}\tWaiting for incoming calls...".format( get_time() ))

        modem.rxThread.join(2**31) # Specify a (huge) timeout so that it essentially blocks indefinitely, but still receives CTRL+C interrupt signal

    except Exception as e:

        error_msg = str(repr(e))

        print("{0}\tGot error '{1}'".format( get_time(), error_msg ))

        publish_message(ERROR_TOPIC_NAME, error_msg)

    finally:
        modem.close()

def main():
    run()

main()
