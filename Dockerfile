FROM python:3.11-slim

RUN pip install --no-cache-dir \
        paho-mqtt \
        garminconnect \
        curl_cffi

WORKDIR /opt/xmtg

COPY xmtg.py /opt/xmtg/
COPY entrypoint.sh /
COPY cmd.sh /

RUN chmod +x /entrypoint.sh /cmd.sh

# Persistent storage for Garmin DI OAuth tokens
ENV GARMIN_TOKENSTORE=/data/garminconnect
VOLUME ["/data/garminconnect"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]
