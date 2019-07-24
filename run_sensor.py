
import argparse
import datetime
import json
import requests
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
	# TODO: Try this, and if it fails, add to_send back to count
	response = requests.post(
		'https://tempis.servicebus.windows.net/production-counts/messages',
		headers={'Authorization':token['token']},
		json={'quantity':to_send,'sensorId':id,'timestamp':datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
	)
	pass


def refresh_access_token():
	global token
	print("Getting access token")
	response = requests.post(
		'https://www.tempis.co.uk/api/SensorTokens', 
		json={'Id':id,'Secret':secret}
	)
	token = response.json()
	token['expires'] = parse(token['expires'])
	print("Access token retrieved")
	return
	

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
