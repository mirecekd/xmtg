# xmtg (Xiaomi MQTT to GarminConnect)

Using lolouk44/xiaomi_mi_scale, jaroslawhartman/withings-garmin-v2 and La0/garmin-uploader to automatically upload data from xiaomi smart scales via MQTT to https://connect.garmin.com

## Build image:

```
docker build -t mirecekd/xmtg .
```

## Run image:
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
