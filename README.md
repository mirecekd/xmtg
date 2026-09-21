# xmtg (Xiaomi Mi smart scale MQTT To Garmin connect)

Docker container that bridges body-composition measurements from a Xiaomi
Mi Smart Scale (and other BLE-capable smart scales) read via ESPHome / MQTT
into [Garmin Connect](https://connect.garmin.com).

Tested on Python 3.11.

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mirecekdg) [!["PayPal.me"](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.me/mirecekd)

</div>

## How it works

1. ESPHome reads the Xiaomi Mi Scale over BLE and publishes a JSON payload
   (`Weight`, `BMI`, `Body Fat`, `Water`, `Muscle Mass`, `Bone Mass`,
   `Visceral Fat`, `Basal Metabolism`, `Metabolic Age`, `TimeStamp`, …) to
   an MQTT topic.
2. `xmtg` subscribes to the topic. On startup it logs in to Garmin Connect
   once. Tokens (DI OAuth) are persisted to `/data/garminconnect` so
   subsequent restarts do not re-authenticate. This avoids Garmin
   rate-limits.
3. Every received message is parsed and uploaded via the `garminconnect`
   library (`add_body_composition`). Duplicate / unavailable readings are
   skipped automatically.

## Get the image

Pre-built multi-arch images (`linux/amd64`, `linux/arm64`) are published
to GitHub Container Registry by GitHub Actions:

```bash
docker pull ghcr.io/mirecekd/xmtg:latest
```

Available tags:

- `latest` — newest commit on `main`
- `vX.Y.Z` / `X.Y` — released versions
- `sha-<commit>` — exact commit

### Build locally (optional)

```bash
git clone https://github.com/mirecekd/xmtg
cd xmtg
docker build -t mirecekd/xmtg .
```

## Run

Create a Docker volume for the persisted Garmin tokens (one-off):

```bash
docker volume create xmtg_garmin_tokens
```

Run the container (replace values):

```bash
docker run -d \
  --name xmtg \
  --restart unless-stopped \
  -e MQTT_BROKER=127.0.0.1 \
  -e MQTT_PORT=1883 \
  -e MQTT_USER=xmtg \
  -e MQTT_PASS=xmtg_secret \
  -e MQTT_TOPIC=miscale/USER/weight \
  -e MQTT_TTL=60 \
  -e GARMIN_USER=yourmail@domain.com \
  -e GARMIN_PASS=t0p53cr3t \
  -v xmtg_garmin_tokens:/data/garminconnect \
  ghcr.io/mirecekd/xmtg:latest
```

On the first start the container performs a credential login to Garmin
Connect and saves OAuth tokens into the volume. Every later restart (or
image upgrade) reuses those tokens and does not log in again.

> **Note:** Garmin accounts with MFA enabled are not currently supported
> by this container — credential login here is non-interactive.

### Multiple users on the same host

Run one container per Garmin account, each with its **own** named token
volume so the OAuth tokens don't collide:

```bash
# Container 1 (Mirecek)
docker run -d --name xmtg-mirecek --restart unless-stopped \
  -e MQTT_BROKER=192.168.0.10 -e MQTT_PORT=1883 \
  -e MQTT_USER=... -e MQTT_PASS=... \
  -e MQTT_TOPIC=miscale/Mirecek/weight -e MQTT_TTL=60 \
  -e GARMIN_USER=... -e GARMIN_PASS=... \
  -v xmtg-mirecek_garmin_tokens:/data/garminconnect \
  ghcr.io/mirecekd/xmtg:latest

# Container 2 (Lucinka)
docker run -d --name xmtg-lucinka --restart unless-stopped \
  -e ... \
  -v xmtg-lucinka_garmin_tokens:/data/garminconnect \
  ghcr.io/mirecekd/xmtg:latest
```

### Synology

On a Synology NAS the same `docker run` command works over SSH. In
Container Manager just create a named volume / shared folder mount for
`/data/garminconnect`.

## Environment variables

| Variable             | Required | Default                | Description                                    |
|----------------------|:--------:|------------------------|------------------------------------------------|
| `MQTT_BROKER`        |    yes   | —                      | MQTT broker host                               |
| `MQTT_PORT`          |    yes   | —                      | MQTT broker port                               |
| `MQTT_USER`          |    yes   | —                      | MQTT username (also used as `client_id`)       |
| `MQTT_PASS`          |    yes   | —                      | MQTT password                                  |
| `MQTT_TOPIC`         |    yes   | —                      | Topic to subscribe                             |
| `MQTT_TTL`           |    yes   | —                      | MQTT keep-alive (seconds)                      |
| `GARMIN_USER`        |    yes   | —                      | Garmin Connect e-mail                          |
| `GARMIN_PASS`        |    yes   | —                      | Garmin Connect password                        |
| `GARMIN_TOKENSTORE`  |    no    | `/data/garminconnect`  | Directory used for persisted DI OAuth tokens   |
| `VERBOSE`            |    no    | `false`                | Set to `1`/`true` to enable DEBUG logging      |

## Expected MQTT payload

```json
{
  "TimeStamp": "2025-01-01 08:30:00",
  "Weight": 78.4,
  "BMI": 24.1,
  "Body Fat": 18.7,
  "Water": 56.2,
  "Muscle Mass": 60.1,
  "Bone Mass": 3.2,
  "Visceral Fat": 8.0,
  "Visceral Fat Rating": 8,
  "Basal Metabolism": 1734,
  "Metabolic Age": 31,
  "Lean Body Mass": 63.7,
  "Protein": 17.2
}
```

If any of `Weight`/`BMI`/`Body Fat` is the literal string `"unavailable"`,
the message is ignored. Identical consecutive payloads are deduplicated.

## v3 workflow

1. ESPHome reads data from Xiaomi Mi Scale and pushes data to an MQTT
   topic.
2. `xmtg` subscribes to that topic and uploads each measurement to Garmin
   Connect.

## Support

If this project saves you time, consider buying me a coffee or sending a
tip — it helps keep things going.

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mirecekdg) [!["PayPal.me"](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.me/mirecekd)

</div>

## Credits

- **lolouk44** — original Xiaomi body-scale BLE reader:
  <https://github.com/lolouk44/xiaomi_mi_scale>
- **Jarek Hartman & Masayuki Hamasaki** — Garmin ANT+ FIT file work:
  <https://github.com/jaroslawhartman/withings-garmin-v2>,
  <https://github.com/jaroslawhartman/withings-sync>
- **Bastien Abadie** — original Garmin Connect uploader:
  <https://github.com/La0/garmin-uploader>
- **cyberjunky** — `python-garminconnect` library that powers the
  current upload path: <https://github.com/cyberjunky/python-garminconnect>

## License

MIT — see [LICENSE](LICENSE).
