#!/usr/local/bin/python3

import paho.mqtt.client as mqtt
import json
import os
import subprocess
import time
import logging
import sys

from datetime import datetime
from garmin import GarminConnect
from fit import FitEncoder_Weight

broker=		os.environ['MQTT_BROKER']
port=	    int(os.environ['MQTT_PORT'])
username=	os.environ['MQTT_USER']
password=	os.environ['MQTT_PASS']
timelive=   int(os.environ['MQTT_TTL'])
topic=		os.environ['MQTT_TOPIC']
garmin_user=	os.environ['GARMIN_USER']
garmin_pass=	os.environ['GARMIN_PASS']
verbose = False

logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)


def on_connect(client, userdata, flags, rc):
  print ("Connected with result code "+str(rc))
  client.subscribe(topic)

def on_message(client, userdata, msg):
  print (msg.payload.decode())

  data = json.loads(msg.payload.decode())

  values = {
    'timestamp': None,
    'weight': None,
    'percent_fat': None,
    'muscle_mass': None,
    'bone_mass': None,
    'percent_hydration': None,
    'active_met': None,
    'metabolic_age': None,
    'basal_met': None,
    'visceral_fat_mass': None,
    'visceral_fat_rating': None,
    'physique_rating': None,
    'bmi': None,
  }

  print("MQTT payload decoded")

  values['timestamp'] = datetime.now()
  values['weight'] = float(data["Weight"])
  values['percent_fat'] = float(data["Body Fat"])
  values['muscle_mass'] = float(data["Muscle Mass"])
  values['bone_mass'] = float(data["Bone Mass"])
  values['percent_hydration'] = float(data["Water"])
  values['metabolic_age'] = int(data["Metabolic Age"])
  values['basal_met'] = float(data["Basal Metabolism"])
  values['visceral_fat_rating'] = int(data["Visceral Fat"])
  values['bmi'] = float(data["BMI"])

  print(values)

  fit = FitEncoder_Weight()
  fit.write_file_info()
  fit.write_file_creator()
  fit.write_weight_scale(**values)
  fit.finish()

  print("FIT file data size %d" % fit.get_size())

  filename = '/tmp/wscale_%s.fit' % values['timestamp'].strftime('%Y-%m-%d-%H-%M')
  a = open(filename, 'wb')
  a.write(fit.getvalue())
  print("File %s written (for debug purposes or just for fun or garmin manual upload" % filename)
  a.close()

  garmin = GarminConnect()
  session = garmin.login(garmin_user, garmin_pass)
  r = garmin.upload_file(fit.getvalue(), session)
  if r:
    print('Fit file uploaded to Garmin Connect')

client = mqtt.Client(username)
client.username_pw_set(username,password)
client.connect(broker,port,timelive)
client.on_connect = on_connect
client.on_message = on_message
client.loop_forever()
