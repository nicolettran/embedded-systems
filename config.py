# config.py
class Config:
    GPIO_MODE = "BCM"  # "BCM" or "BOARD"

    # PIR sensors (BCM)
    PIR1_PIN = 18
    PIR2_PIN = 19

    # LEDs (BCM)
    YELLOW_LED_PIN = 27
    GREEN_LED_PIN = 17

    # Buzzer (BCM)
    BUZZER_PIN = 4

    # Timing
    RFID_TIMEOUT_SEC = 10
    ALARM_DURATION_SEC = 2
    COOLDOWN_SEC = 16
    PIR_DEBOUNCE_SEC = 0.5

    # Camera save location
    IMAGE_DIR = "/home/pi/Project1/intruder_photos"

    # ThingSpeak
    THINGSPEAK_WRITE_KEY = "Put personal key here"
    THINGSPEAK_URL = "https://api.thingspeak.com/update"

    # ThingSpeak fields:
    # field1 Motion (0/1)
    # field2 RFID (1 auth / 0 unauth)
    # field3 Alarm (1/0)
    # field4 Image captured (1/0)
    # field5 Sensor ID (1 or 2)
    AUTHORIZED_UIDS = {"112354582793"}  # replace with your tag UID(s)
