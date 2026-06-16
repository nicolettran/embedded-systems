# hardware.py
import os
import time
from datetime import datetime

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera2 import Picamera2


class LEDPair:
    def __init__(self, yellow_pin: int, green_pin: int):
        self.yellow_pin = yellow_pin
        self.green_pin = green_pin
        GPIO.setup(self.yellow_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.green_pin, GPIO.OUT, initial=GPIO.LOW)

    def set_status(self, authorized: bool):
        GPIO.output(self.green_pin, GPIO.HIGH if authorized else GPIO.LOW)
        GPIO.output(self.yellow_pin, GPIO.LOW if authorized else GPIO.HIGH)

    def off(self):
        GPIO.output(self.yellow_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.LOW)


class Buzzer:
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)

    def beep(self, seconds: float, pattern_hz: float = 6.0):
        period = 1.0 / pattern_hz
        end = time.time() + seconds
        while time.time() < end:
            self.on()
            time.sleep(period / 2)
            self.off()
            time.sleep(period / 2)


class PIRSensor:
    def __init__(self, pin: int, name: str, debounce_sec: float = 0.3):
        self.pin = pin
        self.name = name
        self.debounce_sec = debounce_sec
        GPIO.setup(self.pin, GPIO.IN)
        self._last_trigger = 0.0

    def motion_detected(self) -> bool:
        now = time.time()
        if GPIO.input(self.pin) == GPIO.HIGH and (now - self._last_trigger) > self.debounce_sec:
            self._last_trigger = now
            return True
        return False


class RFIDAuth:
    def __init__(self, authorized_uids: set[str]):
        self.reader = SimpleMFRC522()
        self.authorized_uids = {str(x).strip() for x in authorized_uids}

    def read_blocking(self):
        uid, text = self.reader.read()
        return str(uid), text

    def is_authorized(self, uid: str) -> bool:
        return str(uid).strip() in self.authorized_uids


class Camera:
    def __init__(self, image_dir: str):
        self.image_dir = image_dir
        os.makedirs(self.image_dir, exist_ok=True)
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_still_configuration())
        self.picam2.start()
        time.sleep(1.0)

    def capture(self, prefix: str = "intruder") -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.image_dir, f"{prefix}_{ts}.jpg")
        self.picam2.capture_file(path)
        return path

    def close(self):
        try:
            self.picam2.stop()
        except Exception:
            pass
