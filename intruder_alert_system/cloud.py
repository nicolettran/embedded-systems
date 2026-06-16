# cloud.py
import requests

class ThingSpeakClient:
    def __init__(self, write_key: str, url: str):
        self.write_key = write_key
        self.url = url

    def send_event(self, motion: int, rfid_ok: int, alarm: int, image: int, sensor_id: int) -> bool:
        payload = {
            "api_key": self.write_key,
            "field1": motion,
            "field2": rfid_ok,
            "field3": alarm,
            "field4": image,
            "field5": sensor_id,
        }
        try:
            r = requests.post(self.url, data=payload, timeout=6)
            return r.status_code == 200 and r.text.strip() != "0"
        except Exception:
            return False
