#!/usr/bin/python

import serial
import paho.mqtt.client as mqtt
import re
import logging
from enum import Enum
from typing import Any, Callable, Dict, Generator, cast


serialdev = '/dev/ttyACM0'
broker = 'x.x.x.x'
DELIM = ';'

logger = logging.getLogger('rflink2mqtt')
hdlr = logging.FileHandler('/var/log/rflink2mqtt.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
#logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)

ser = serial.Serial(
        port=serialdev,
        baudrate = 57600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=None
)

ser.flushInput()
ser.flushOutput()

#def signed_to_float(hex: str) -> float:
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
        client.subscribe("rflink/tx",0)

def on_message(client, userdata, message):
	#print ("Send to RFLINK " + str(message.payload.decode("utf-8")))
	logging.info("Send to RFLINK " + str(message.payload.decode("utf-8")))
	#my_logger.debug("Send to RFLINK: " + str(message.payload.decode("utf-8")))
        ser.write( str(message.payload.decode("utf-8"))+"\r\n")

def decode_packet(packet):
	#print ("DEBUG: " + packet)
	logger.debug(packet)
	try:
		node_id, _, protocol, attrs = x.split(DELIM, 3)
	except ValueError:
		#logging.warn("Could not split line: %s", line)
		#print ("Could not split line: %s", packet)
		logger.error("Could not split line: " + packet)
		return

	#print ("node_id: " + node_id + "\n")
	logger.info("node_id: " + node_id)
	#print ("protocol: " + protocol + "\n")
	logger.info("protocol: " + protocol)
	switch = None
	find = 0
	for attr in filter(None, attrs.strip(DELIM).split(DELIM)):
		key, value = attr.lower().split('=')
		find = 1
		#print ("key is : " + key + " / Value is : " + value )
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
				#print "rflink/%s/%s/%s / value: %s" % (name, id, switch, value)
				logger.info("rflink/" + str(name) + "/" + str(id) + "/" + str(switch) + " / value: " + str(value))
			else:
				client.publish("rflink/"+name+"/"+id, value, 0)
				#print "rflink/%s/%s / value: %s" % (name, id, value)
				logger.info("rflink/" + str(name) + "/" + str(id) + " / value: " + str(value))
		
	if find == 0:
		client.publish("rflink/rx", packet, 0)
		#print ("not find protocol of other: " + packet)
		logger.error("not find protocol of other: " + packet)
		
	return 


client = mqtt.Client()
client.connect(broker, 1883)
client.on_connect = on_connect
client.on_message = on_message
client.loop_start()

while True:
        x=ser.readline()
        x = x.strip("\r\n")
	decode_packet(x)
	#print ("Received from RFLINK " + x)
        #client.publish("rflink/rx", x, 0)
