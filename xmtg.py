"""xmtg — Bridge Xiaomi Mi Smart Scale telemetry from MQTT to Garmin Connect.

Listens to an MQTT topic for body-composition measurements and uploads them
to Garmin Connect. Uses token-based authentication (DI OAuth) with persistent
token storage so we do not re-authenticate on every message (Garmin would
rate-limit the IP otherwise).
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# --- Configuration --------------------------------------------------------- #

broker = os.environ["MQTT_BROKER"]
port = int(os.environ["MQTT_PORT"])
mqtt_user = os.environ["MQTT_USER"]
mqtt_pass = os.environ["MQTT_PASS"]
timelive = int(os.environ["MQTT_TTL"])
topic = os.environ["MQTT_TOPIC"]
garmin_user = os.environ["GARMIN_USER"]
garmin_pass = os.environ["GARMIN_PASS"]
tokenstore = os.environ.get("GARMIN_TOKENSTORE", "/data/garminconnect")
tokenstore_path = str(Path(tokenstore).expanduser())

verbose = os.environ.get("VERBOSE", "").lower() in ("1", "true", "yes")

logging.basicConfig(
    level=logging.DEBUG if verbose else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("xmtg")

previous_data = None
garmin: Garmin | None = None


# --- Garmin authentication ------------------------------------------------- #

def init_garmin() -> Garmin:
    """Initialise Garmin API client.

    1. Try to reuse persisted DI OAuth tokens from ``tokenstore_path``.
    2. Fallback to credential login (without MFA) and save tokens for
       future runs.
    """
    Path(tokenstore_path).mkdir(parents=True, exist_ok=True)

    # 1) Try existing tokens
    try:
        g = Garmin()
        g.login(tokenstore_path)
        log.info("Garmin: logged in using saved tokens (%s)", tokenstore_path)
        return g
    except (
        FileNotFoundError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ) as exc:
        log.info("Garmin: no valid token found (%s) — falling back to credentials", exc)

    # 2) Credential login — save tokens
    g = Garmin(email=garmin_user, password=garmin_pass)
    g.login(tokenstore_path)
    log.info("Garmin: credential login successful, tokens saved to %s", tokenstore_path)
    return g


def ensure_garmin() -> Garmin:
    """Return a usable Garmin client, re-initialising on demand."""
    global garmin
    if garmin is None:
        garmin = init_garmin()
    return garmin


# --- MQTT callbacks -------------------------------------------------------- #

def on_connect(client, userdata, flags, rc):
    log.info("MQTT connected (rc=%s), subscribing to %s", rc, topic)
    client.subscribe(topic)


def _is_unavailable(value) -> bool:
    return isinstance(value, str) and value.strip().lower() == "unavailable"


def on_message(client, userdata, msg):
    global previous_data, garmin

    payload_text = msg.payload.decode()
    log.debug("MQTT payload: %s", payload_text)

    try:
        data = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        log.error("MQTT payload is not valid JSON: %s", exc)
        return

    if previous_data is not None and previous_data == data:
        log.info("Data unchanged — skipping upload")
        return

    # If any of the headline values is "unavailable", skip the whole sample.
    if any(_is_unavailable(data.get(k)) for k in ("Weight", "BMI", "Body Fat")):
        log.info("Skipping upload: some values are unavailable")
        return

    try:
        weight = float(data["Weight"])
        bmi = float(data["BMI"])
        basal_met = float(data["Basal Metabolism"])
        visceral_fat_mass = float(data["Visceral Fat"])
        body_fat = float(data["Body Fat"])
        water = float(data["Water"])
        bone_mass = float(data["Bone Mass"])
        muscle_mass = float(data["Muscle Mass"])
        metabolic_age = int(round(float(data["Metabolic Age"])))
    except (KeyError, TypeError, ValueError) as exc:
        log.error("Cannot parse measurement values: %s", exc)
        return

    # Optional / less common fields — pass only when present.
    visceral_fat_rating = data.get("Visceral Fat Rating")
    if visceral_fat_rating is not None and not _is_unavailable(visceral_fat_rating):
        try:
            visceral_fat_rating = int(round(float(visceral_fat_rating)))
        except (TypeError, ValueError):
            visceral_fat_rating = None
    else:
        visceral_fat_rating = None

    log.info(
        "Uploading body composition: weight=%s bmi=%s body_fat=%s water=%s "
        "muscle=%s bone=%s visceral_mass=%s metabolic_age=%s (ts=%s)",
        weight, bmi, body_fat, water, muscle_mass, bone_mass,
        visceral_fat_mass, metabolic_age, data.get("TimeStamp"),
    )

    try:
        upload_body_composition(
            weight=weight,
            bmi=bmi,
            body_fat=body_fat,
            water=water,
            muscle_mass=muscle_mass,
            bone_mass=bone_mass,
            visceral_fat_mass=visceral_fat_mass,
            visceral_fat_rating=visceral_fat_rating,
            basal_met=basal_met,
            metabolic_age=metabolic_age,
        )
        previous_data = data
        log.info("Body composition data uploaded to Garmin Connect")
    except GarminConnectTooManyRequestsError as exc:
        log.error("Garmin rate-limit hit: %s", exc)
    except (GarminConnectAuthenticationError, GarminConnectConnectionError) as exc:
        log.error("Garmin upload failed: %s", exc)


def upload_body_composition(
    *,
    weight: float,
    bmi: float,
    body_fat: float,
    water: float,
    muscle_mass: float,
    bone_mass: float,
    visceral_fat_mass: float,
    visceral_fat_rating,
    basal_met: float,
    metabolic_age: int,
) -> None:
    """Upload body composition; on auth failure re-login once and retry."""
    global garmin
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    kwargs = dict(
        timestamp=timestamp,
        weight=weight,
        percent_fat=body_fat,
        percent_hydration=water,
        visceral_fat_mass=visceral_fat_mass,
        bone_mass=bone_mass,
        muscle_mass=muscle_mass,
        basal_met=basal_met,
        metabolic_age=metabolic_age,
        bmi=bmi,
    )
    if visceral_fat_rating is not None:
        kwargs["visceral_fat_rating"] = visceral_fat_rating

    def _do_upload() -> None:
        ensure_garmin().add_body_composition(**kwargs)

    try:
        _do_upload()
    except GarminConnectAuthenticationError as exc:
        log.warning("Auth error during upload (%s) — re-initialising Garmin client", exc)
        garmin = None
        _do_upload()


# --- Main ------------------------------------------------------------------ #

def main() -> None:
    # Pre-authenticate before we start the MQTT loop so the first message
    # doesn't fight with login latency.
    ensure_garmin()

    client = mqtt.Client(
        client_id=mqtt_user,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
    )
    client.username_pw_set(mqtt_user, mqtt_pass)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, timelive)
    client.loop_forever()


if __name__ == "__main__":
    main()
