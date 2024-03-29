import argparse
import datetime
import time
import json
import requests
import sys
import os
from dateutil.parser import parse
from gpiozero import DigitalInputDevice
from twisted.internet import task, reactor


# Functions
def ensure_config(setting_name, setting_description):
    if setting_name not in config:
        print("Error: %s must be specified in config file" %(setting_description))
        exit(1)
    return config[setting_name]


def send_data():
    global token
    global count
    global sending_errors
    if token is None:
        print("No access token yet, not sending data")
        return
    if token['expires'] < datetime.datetime.now(token['expires'].tzinfo) + datetime.timedelta(minutes=1):
        print("Error: Access token expired!")
        return
    if count == 0:
        return
    print("Sending count: %i" %(count))
    to_send = count
    count = 0
    try:
        response = requests.post(
            'https://tempis-messages.servicebus.windows.net/production-counts/messages',
            headers={'Authorization':token['token']},
            json={'quantity':to_send,'sensorId':id,'timestamp':datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")},
            timeout=5
        )
        sending_errors = 0
    #except requests.exceptions.ConnectionError as e:
    #    print("Error sending update to Tempis, retaining count to send later")
    #    count = count + to_send
    except:
        e = sys.exc_info()[0]
        print(e)
        print("Error sending update to Tempis, retaining count to send later")
        count = count + to_send
        sending_errors = sending_errors + 1
        if sending_errors > 10:
            print("10 errors in a row now, attempting to cycle WiFi")
            os.system("sudo ip link set wlan0 down")
            time.sleep(5)
            os.system("sudo ip link set wlan0 up")
            print("Wifi restarted")
    finally:
        return


def refresh_access_token():
    global token
    print("Getting access token")
    retrieved = False
    connecting_errors = 0
    while not retrieved:
        try:
            response = requests.post(
                'https://www.tempis.co.uk/api/SensorTokens', 
                json={'Id':id,'Secret':secret},
                timeout=5
            )
            token = response.json()
            if response.status_code == 200:
                retrieved = True
            token['expires'] = parse(token['expires'])
            print("Access token retrieved")
            connecting_errors = 0
        except requests.exceptions.ConnectionError as e:
            print("Error connecting to Tempis")
            time.sleep(5)
            connecting_errors = connecting_errors + 1
        except:
            e = sys.exc_info()[0]
            print("Exception encountered getting token")
            print(e)
            connecting_errors = connecting_errors + 1
        finally:
            if connecting_errors > 10:
                print("10 errors in a row now, attempting to cycle WiFi")
                os.system("sudo ip link set wlan0 down")
                time.sleep(5)
                os.system("sudo ip link set wlan0 up")
                print("Wifi restarted")


    

def increment_count():
    global count
    count += 1

# Script starts here
parser = argparse.ArgumentParser(description='Send sensor data to Tempis')
parser.add_argument('config', help='The config file to be used')

args = parser.parse_args()
with open(args.config) as config_file:
    config = json.load(config_file)

# Config variables
GPIO = ensure_config('GPIO', 'GPIO pin')
id = ensure_config('sensor','Sensor id')
secret = ensure_config('secret','Sensor secret')
interval = ensure_config('interval', 'Interval')

# Global state variables
token = None
count = 0
sending_errors = 0

# Actions
print("")
print("")
print("Tempis is running!")
send_data_task = task.LoopingCall(send_data)
send_data_task.start(interval)

get_token_task = task.LoopingCall(refresh_access_token)
get_token_task.start(3600)

sensor = DigitalInputDevice(GPIO)
sensor.when_activated = increment_count

reactor.run()
