FROM python:3.9-alpine

RUN apk add git

RUN pip install paho-mqtt

RUN pip install https://github.com/La0/garmin-uploader/archive/cloudscraper.zip

WORKDIR /opt

RUN git clone https://github.com/mirecekd/xmtg

WORKDIR /opt/xmtg

# Copy in docker scripts to root of container...
COPY entrypoint.sh /
COPY cmd.sh /

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]
