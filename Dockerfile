FROM python:3.9-alpine

RUN pip install paho-mqtt garminconnect

WORKDIR /opt/xmtg

COPY xmtg.py /opt/xmtg

COPY entrypoint.sh /
COPY cmd.sh /

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]
