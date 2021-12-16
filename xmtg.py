#!/usr/local/bin/python3

import paho.mqtt.client as mqtt
import json
import os
import subprocess
import time

from fit import FitEncoder_Weight
from datetime import datetime

broker=		os.environ['MQTT_BROKER']
port=	    int(os.environ['MQTT_PORT'])
username=	os.environ['MQTT_USER']
password=	os.environ['MQTT_PASS']
timelive=   int(os.environ['MQTT_TTL'])
topic=		os.environ['MQTT_TOPIC']
garmin_user=	os.environ['GARMIN_USER']
garmin_pass=	os.environ['GARMIN_PASS']

def on_connect(client, userdata, flags, rc):
  print ("Connected with result code "+str(rc))
  client.subscribe(topic)

def on_message(client, userdata, msg):
  print (msg.payload.decode())
  data = json.loads(msg.payload.decode())

  values = {
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
  }

  values['weight'] = float(data["Weight"])
  values['visceral_fat_mass'] = float(data["Visceral Fat"])
  values['percent_fat'] = float(data["Body Fat"])
  values['percent_hydration'] = float(data["Water"])
  values['bone_mass'] = float(data["Bone Mass"])
  values['muscle_mass'] = float(data["Muscle Mass"])
  values['metabolic_age'] = int(data["Metabolic Age"])

  values['timestamp'] = datetime.now()

  fit = FitEncoder_Weight()
  fit.write_file_info()
#  fit.write_file_creator()
  fit.write_weight_scale(**values)
  fit.finish()
  print("FIT file data size %d" % fit.get_size())

  filename = '/tmp/wscale_%s.fit' % values['timestamp'].strftime('%Y-%m-%d-%H-%M')
  a = open(filename, 'wb')
  a.write(fit.getvalue())
  print("File %s written" % filename)
  a.close()

#  p=subprocess.Popen(["/usr/local/bin/gupload", filename, "-u", garmin_user, "-p", garmin_pass, "-v", "1"])
#  p.wait()

#  os.remove(filename)
#  print("File %s deleted. Waiting for next MQTT msg" % filename)

  finished = False
  while not finished:
    p=subprocess.run(["/usr/local/bin/gupload", filename, "-u", garmin_user, "-p", garmin_pass, "-v", "1"],capture_output=True)
    if p.stdout.find(b'[INFO] Uploaded activity') > 0:
      finished = True
      print ("=-=-=-=-=-=-= SUCCESS =-=-=-=-=-=-=")
      print (p.stdout)
      print ("=-=-=-=-=-=-= SUCCESS =-=-=-=-=-=-=")
    else:
      print ("-- FAIL --")
      print (p.stdout) 
      print ("-- FAIL --")
      time.wait(30)

client = mqtt.Client(username)
client.username_pw_set(username,password)
client.connect(broker,port,timelive)
client.on_connect = on_connect
client.on_message = on_message
client.loop_forever()
