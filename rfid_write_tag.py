# rfid_write_tag.py
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

def write_tag(text: str):
    reader = SimpleMFRC522()
    try:
        print("Place RFID tag to WRITE...")
        reader.write(text)
        print("Write complete.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    write_tag("AUTHORIZED_USER")
