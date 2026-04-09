import numpy as np
import cv2
from os import system
from requests import get


class WaterMeter:

    host_frigate = "192.168.4.81:5000"
    trim_w, trim_h = 0.31, 0.6

    def get_snapshot_content(self):
        r = get(f"http://{self.host_frigate}/api/tech/latest.jpg")
        img = cv2.imdecode(
            np.frombuffer(r.content, np.uint8),
            cv2.IMREAD_COLOR
        )
        poi = cv2.rotate(
            img[0:int(img.shape[0] * self.trim_h), 0:int(img.shape[1] * self.trim_w)],  # noqa: E501
            cv2.ROTATE_90_COUNTERCLOCKWISE
        )
        is_success, buffer = cv2.imencode(".jpg", poi)
        return buffer.tobytes()

    def send_mqtt_with_meter(self, meter_reading):
        system(f'mosquitto_pub -h mqtt -p 1883 -u mqttha -P "$FRIGATE_MQTT_PASSWORD" -t "energy/water" -m "{meter_reading}"')  # noqa: E501
