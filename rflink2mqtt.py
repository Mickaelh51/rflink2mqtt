#!/usr/bin/python3

import serial
import paho.mqtt.client as mqtt
from typing import Any, Callable, Dict, Generator, cast
import os
import logging

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('rflink2mqtt')
logger.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

# Get environment variables
USB_INTERFACE = os.environ.get('USB_INTERFACE')
MQTT_SERVER = os.environ.get('MQTT_SERVER')

serialdev = USB_INTERFACE
broker = MQTT_SERVER
DELIM = ';'

def signed_to_float(hex):
  """Convert signed hexadecimal to floating value."""
  if int(hex, 16) & 0x8000:
      return -(int(hex, 16) & 0x7FFF) / 10.0
  else:
      return int(hex, 16) / 10.0


VALUE_TRANSLATION = cast(Dict[str, Callable], {
  'awinsp': lambda hex: int(hex, 16) / 10,
  'baro': lambda hex: int(hex, 16),
  'bforecast': lambda x: BFORECAST_LOOKUP.get(x, 'Unknown'),
  'chime': int,
  'co2': int,
  'current': int,
  'current2': int,
  'current3': int,
  'dist': int,
  'hstatus': lambda x: HSTATUS_LOOKUP.get(x, 'Unknown'),
  'hum': int,
  'kwatt': lambda hex: int(hex, 16),
  'lux': lambda hex: int(hex, 16),
  'meter': int,
  'rain': lambda hex: int(hex, 16) / 10,
  'rainrate': lambda hex: int(hex, 16) / 10,
  'raintot': lambda hex: int(hex, 16) / 10,
  'sound': int,
  'temp': signed_to_float,
  'uv': lambda hex: int(hex, 16),
  'volt': int,
  'watt': lambda hex: int(hex, 16),
  'winchl': signed_to_float,
  'windir': lambda windir: int(windir) * 22.5,
  'wings': lambda hex: int(hex, 16) / 10,
  'winsp': lambda hex: int(hex, 16) / 10,
  'wintmp': signed_to_float,
})

PACKET_FIELDS = {
  'awinsp': 'average_windspeed',
  'baro': 'barometric_pressure',
  'bat': 'battery',
  'bforecast': 'weather_forecast',
  'chime': 'doorbell_melody',
  'cmd': 'command',
  'co2': 'co2_air_quality',
  'current': 'current_phase_1',
  'current2': 'current_phase_2',
  'current3': 'current_phase_3',
  'dist': 'distance',
  'fw': 'firmware',
  'hstatus': 'humidity_status',
  'hum': 'humidity',
  'hw': 'hardware',
  'kwatt': 'kilowatt',
  'lux': 'light_intensity',
  'meter': 'meter_value',
  'rain': 'total_rain',
  'rainrate': 'rain_rate',
  'raintot': 'total_rain',
  'rev': 'revision',
  'sound': 'noise_level',
  'temp': 'temperature',
  'uv': 'uv_intensity',
  'ver': 'version',
  'volt': 'voltage',
  'watt': 'watt',
  'winchl': 'windchill',
  'windir': 'winddirection',
  'wings': 'windgusts',
  'winsp': 'windspeed',
  'wintmp': 'windtemp',
}

HSTATUS_LOOKUP = {
  '0': 'normal',
  '1': 'comfortable',
  '2': 'dry',
  '3': 'wet',
}
BFORECAST_LOOKUP = {
  '0': 'no_info',
  '1': 'sunny',
  '2': 'partly_cloudy',
  '3': 'cloudy',
  '4': 'rain',
}

def on_connect(client, userdata, flags, rc):
  logger.info(f"Connected with result to host:{MQTT_SERVER} , code:{rc}")
  client.subscribe("rflink2/tx",0)
  logger.info(f"subscribed to: rflink2/tx")

def on_message(client, userdata, message):
	logger.info(f"Send to RFLINK " + str(message.payload.decode("utf-8")))
	ser.write(message.payload + "\r\n".encode('utf-8'))

def decode_packet(packet):
	try:
		node_id, _, protocol, attrs = x.split(DELIM, 3)
	except ValueError:
		logger.error(f"Could not split line: {packet}")
		return

	logger.info(f"node_id:{node_id}, protocol: {protocol}")
	switch = None
	find = 0
	for attr in filter(None, attrs.strip(DELIM).split(DELIM)):
		key, value = attr.lower().split('=')
		find = 1
		if key in VALUE_TRANSLATION:
			value = VALUE_TRANSLATION.get(key)(value)
		name = PACKET_FIELDS.get(key, key)
		if key == "id":
			id = value
		elif key == "switch":
			switch = value
		else:
			if switch:
				client.publish("rflink/"+name+"/"+id+"/"+switch, value, 0)
				logger.info("rflink/%s/%s/%s / value: %s" % (name, id, switch, value))
			else:
				client.publish("rflink/"+name+"/"+id, value, 0)
				logger.info("rflink/%s/%s / value: %s" % (name, id, value))
		
	if find == 0:
		client.publish("rflink/rx", packet, 0)
		logger.error(f"not find protocol of other: {packet}")
		
	return 



if __name__ == '__main__':

  ser = serial.Serial(
  port=serialdev,
  baudrate = 57600,
  parity=serial.PARITY_NONE,
  stopbits=serial.STOPBITS_ONE,
  bytesize=serial.EIGHTBITS,
  timeout=None
)

  try:
    ser.flushInput()
    ser.flushOutput()
    logger.info(f"Connected to device:{USB_INTERFACE}")
  except:
    logger.error(f"Not possible to flash device:{USB_INTERFACE}")


  client = mqtt.Client()
  client.connect(broker, 1883)
  client.on_connect = on_connect
  client.on_message = on_message
  client.loop_start()

  while True:
    x=ser.readline()
    x = x.decode("utf-8").strip("\r\n")
    try:
        decode_packet(x)
    except ValueError:
      logger.error("Error in decode packet")
