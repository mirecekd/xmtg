FROM python:3.8-alpine

RUN apk add git

RUN pip install garmin-uploader paho-mqtt

WORKDIR /opt

RUN git clone https://github.com/mirecekd/xmtg

WORKDIR /opt/xmtg

# Copy in docker scripts to root of container...
COPY entrypoint.sh /
COPY cmd.sh /

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]
