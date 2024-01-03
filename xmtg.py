import paho.mqtt.client as mqtt
import json
import os
import logging
import sys

from datetime import datetime

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

broker = os.environ['MQTT_BROKER']
port = int(os.environ['MQTT_PORT'])
username = os.environ['MQTT_USER']
password = os.environ['MQTT_PASS']
timelive = int(os.environ['MQTT_TTL'])
topic = os.environ['MQTT_TOPIC']
garmin_user = os.environ['GARMIN_USER']
garmin_pass = os.environ['GARMIN_PASS']
verbose = False
previous_data = None

logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(topic)


def on_message(client, userdata, msg):
    global previous_data
    print(msg.payload.decode())

    data = json.loads(msg.payload.decode())

    if previous_data is not None and previous_data == data:
      print("Data has not changed. Skipping upload.")
      return

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

    values['timestamp'] = data['TimeStamp']
    values['weight'] = float(data["Weight"])
    values['bmi'] = float(data["BMI"])    
    values['basal_met'] = float(data["Basal Metabolism"])
    values['visceral_fat_mass'] = float(data["Visceral Fat"])
    values['lean_body_mass'] = float(data["Lean Body Mass"])
    values['body_fat'] = float(data["Body Fat"])
    values['water'] = float(data["Water"])
    values['bone_mass'] = float(data["Bone Mass"])    
    values['muscle_mass'] = float(data["Muscle Mass"])
    values['protein'] = float(data["Protein"])
    values['metabolic_age'] = int(data["Metabolic Age"])

    print(values)

    garmin = Garmin(garmin_user, garmin_pass)
    garmin.login()
    garmin.add_body_composition(
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        weight=values['weight'],
        percent_fat=values['body_fat'],
        percent_hydration=values['water'],
        visceral_fat_mass=values['visceral_fat_mass'],
        bone_mass=values['bone_mass'],
        muscle_mass=values['muscle_mass'],
        basal_met=values['basal_met'],
        metabolic_age=values['metabolic_age'],
        visceral_fat_rating=values['visceral_fat_mass'],
        bmi=values['bmi']
    )

    print('Body composition data uploaded to Garmin Connect')

    previous_data = data


client = mqtt.Client(username)
client.username_pw_set(username, password)
client.connect(broker, port, timelive)
client.on_connect = on_connect
client.on_message = on_message
client.loop_forever()