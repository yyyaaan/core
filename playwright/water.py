from os import system
from requests import get, post

class WaterMeter:

    def get_snapshot_content(self):
        r = get("http://frigate:5000/api/tech/latest.jpg")
        return r.content

    def send_mqtt_with_meter(self, meter_reading):
        system(f'mosquitto_pub -h mqtt -p 1883 -u mqttha -P "$FRIGATE_MQTT_PASSWORD" -t "energy/water" -m "{meter_reading}"')
