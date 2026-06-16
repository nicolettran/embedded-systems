# main.py
import RPi.GPIO as GPIO
from config import Config
from system import IntruderDetectionSystem

def main():
    GPIO.setwarnings(False)
    if Config.GPIO_MODE == "BCM":
        GPIO.setmode(GPIO.BCM)
    else:
        GPIO.setmode(GPIO.BOARD)

    system = IntruderDetectionSystem(Config)
    system.run()

if __name__ == "__main__":
    main()
