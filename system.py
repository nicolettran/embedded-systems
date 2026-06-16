# system.py
import time
import queue
import threading
from datetime import datetime

import RPi.GPIO as GPIO

from hardware import LEDPair, Buzzer, PIRSensor, RFIDAuth, Camera
from cloud import ThingSpeakClient


class IntruderDetectionSystem:
    def __init__(self, cfg):
        self.cfg = cfg
        self.leds = LEDPair(cfg.YELLOW_LED_PIN, cfg.GREEN_LED_PIN)
        self.buzzer = Buzzer(cfg.BUZZER_PIN)
        self.pir1 = PIRSensor(cfg.PIR1_PIN, "PIR1", cfg.PIR_DEBOUNCE_SEC)
        self.pir2 = PIRSensor(cfg.PIR2_PIN, "PIR2", cfg.PIR_DEBOUNCE_SEC)
        self.rfid = RFIDAuth(cfg.AUTHORIZED_UIDS)
        self.cam = Camera(cfg.IMAGE_DIR)
        self.cloud = ThingSpeakClient(cfg.THINGSPEAK_WRITE_KEY, cfg.THINGSPEAK_URL)
        self._last_event_time = 0.0

    def _log(self, msg: str):
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")

    def _cooldown_ok(self) -> bool:
        return (time.time() - self._last_event_time) > self.cfg.COOLDOWN_SEC

    def _wait_for_rfid_with_timeout(self, timeout_sec: int):
        q = queue.Queue()

        def _read():
            try:
                uid, _ = self.rfid.read_blocking()
                q.put(uid)
            except Exception:
                q.put(None)

        t = threading.Thread(target=_read, daemon=True)
        t.start()

        try:
            uid = q.get(timeout=timeout_sec)
        except queue.Empty:
            return None
        return uid

    def handle_motion_event(self, sensor_id: int):
        if not self._cooldown_ok():
            return
        self._last_event_time = time.time()

        self._log(f"Motion detected on PIR {sensor_id}. Waiting for RFID...")
        self.leds.off()
        
        self.rfid = RFIDAuth(self.cfg.AUTHORIZED_UIDS)
        
        uid = self._wait_for_rfid_with_timeout(self.cfg.RFID_TIMEOUT_SEC)
        authorized = (uid is not None) and self.rfid.is_authorized(uid)

        if authorized:
            self._log(f"AUTHORIZED (UID={uid})")
            self.leds.set_status(True)

            sent = self.cloud.send_event(
            motion=1,
            rfid_ok=1,
            alarm=0,
            image=0,
            sensor_id=sensor_id
            )

            self._log(f"ThingSpeak upload (AUTHORIZED): {'OK' if sent else 'FAILED'}")

            time.sleep(2)
            self.leds.off()
            return

        self._log(f"UNAUTHORIZED USER or NO RFID WAS READ (UID={uid}) \nActivating alarm and taking a photo!!")
        self.leds.set_status(False)

        image_ok = 0
        try:
            path = self.cam.capture(prefix=f"intruder_pir{sensor_id}")
            image_ok = 1
            self._log(f"Captured: {path}")
        except Exception as e:
            self._log(f"Camera failed: {e}")

        self.buzzer.beep(self.cfg.ALARM_DURATION_SEC, pattern_hz=7)

        sent = self.cloud.send_event(motion=1, rfid_ok=0, alarm=1, image=image_ok, sensor_id=sensor_id)
        self._log(f"ThingSpeak upload (UNAUTHORIZED): {'OK' if sent else 'FAILED'}")

        self.leds.off()
        self.buzzer.off()

    def run(self):
        self._log("System running. Monitoring PIR sensors...")
        try:
            while True:
                if self.pir1.motion_detected():
                    self.handle_motion_event(sensor_id=1)
                if self.pir2.motion_detected():
                    self.handle_motion_event(sensor_id=2)
                time.sleep(0.05)
        finally:
            self.shutdown()

    def shutdown(self):
        self._log("Shutting down...")
        try:
            self.cam.close()
        except Exception:
            pass
        self.leds.off()
        self.buzzer.off()
        GPIO.cleanup()
