# xmtg (Xiaomi smart scale Mqtt To Garmin connect)

Docker container to upload data from Xiaomi Mi Smart Scale (and other bluetooth capable smart scales) to https://connect.garmin.com. 

Tested on Python 3.11 

## Build image:

clone this repo and build container
```
git clone https://github.com/mirecekd/xmtg
cd xmtg
docker build -t mirecekd/xmtg .
```

## Run container:
(use your values)


```
docker run --name=xmtg \
  -e "MQTT_BROKER=127.0.0.1" \
  -e "MQTT_PORT=1883" \
  -e "MQTT_USER=xmtg" \
  -e "MQTT_PASS=xmtg_secret" \
  -e "MQTT_TOPIC=miscale/USER/weight" \
  -e "MQTT_TTL=60" \
  -e "GARMIN_USER=yourmail@domain.com" \
  -e "GARMIN_PASS=t0p53cr3t" \
  --restart always \
  mirecekd/xmtg
```
# v3
## Workflow

1. ESPHome reads data from Xiaomi Mi Scale and pushes data to MQTT topic
1. xmtg reads topic and pushes data to Garmin Connect


# obsolete: v2

## Configure Xiaomi Mi Scale
Follow instructions on lolouk44's [page](https://github.com/lolouk44/xiaomi_mi_scale)

## Configure Garmin Connect
Follow instructions on Bastien's [page](https://github.com/La0/garmin-uploader#garmin-connect-account)

# Credits

## lolouk44 
for Code to read weight measurements from Xiaomi Body Scales - https://github.com/lolouk44/xiaomi_mi_scale

## Jarek Hartman & Masayuki Hamasaki
for library which I am using to create Garmin ANT+ FIT files - https://github.com/jaroslawhartman/withings-garmin-v2, in v2 version I am using https://github.com/jaroslawhartman/withings-sync.git

Parts of Jarek's work is based on 

## Bastien Abadie
for library for upload files to https://connect.garmin.com - https://github.com/La0/garmin-uploader
