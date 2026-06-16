import RPi.GPIO as GPIO     # Import Library to access GPIO PIN
import time                 # To access delay function
import requests
import http.client as httplib
import urllib.parse


GPIO.setmode(GPIO.BCM)    # Consider complete raspberry-pi board
GPIO.setwarnings(False)     # To avoid same PIN use warning              
TRIG = 21                   # Define PIN for Trigger pinb
ECHO = 20                    # Define PIN for Echo pin
Relay_PIN = 13                 # Define PIN for Relay
Buzzer = 4
Yellow_LED = 27 
GPIO.setup(ECHO,GPIO.IN)   # Set pin function as input  
GPIO.setup(TRIG,GPIO.OUT)   # Set pin function as output
GPIO.setup(Relay_PIN,GPIO.OUT)   # Set pin function as output
GPIO.setup(Yellow_LED,GPIO.OUT)
GPIO.setup(Buzzer,GPIO.OUT)
GPIO.output(Relay_PIN, False)   #Turn Off Relay

GPIO.output(Buzzer, False)   #Turn Off Buzzer
GPIO.output(Yellow_LED, False)   #Turn Off LED
GPIO.output(TRIG, False)


print ("Waiting for sensor to settle")
time.sleep(1)
while (True):
    # To start trasmit the sound from ultrasonic sensor
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    # To record the current time when Echo pin is low
    while GPIO.input(ECHO)==0:
        pulse_start = time.time()
    #To recored the latest time when Echo pin is set to high when trasmitted sound detected    
    while GPIO.input(ECHO)==1:
        pulse_end = time.time()   
    # To find out time difference between trasmit and received sound point
    pulse_duration = pulse_end - pulse_start
    # Now speed is distance / time
    # we know speed of sounnd is 343 m/s
    # we know the time then calculate distance by using formula
    #17150 = 34300 /2  (2 factor becuase we require one side distace from obstacle)
    distance = pulse_duration * 17150
    distance = round(distance, 2)

    print ("Water Level " + str(distance))
    time.sleep(0.5)
    
    #setup pushover API
    app_key = "Put personal key here"
    user_key = "Put personal key here"

    #Message to be sent via Pushover
    PUSH_MSG = "Water level below threshold"
    
    def sendPush(PUSH_MSG):
        conn = httplib.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": app_key,
                         "user": user_key,
                         "message": PUSH_MSG,
                         }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()
        return

    if(distance < 8):
        GPIO.output(Relay_PIN, True)   #Turn Off relay
        time.sleep(0.00001)
        GPIO.output(Yellow_LED, False)
        time.sleep(0.00001)
        GPIO.output(Buzzer, False)
        time.sleep(0.00001)
        print ("Motor Off")
        time.sleep(0.2)
    else:
        GPIO.output(Relay_PIN, False)   #Turn ON relay
        time.sleep(0.2)
        GPIO.output(Yellow_LED, True)
        time.sleep(0.00001)
        GPIO.output(Buzzer, True)
        time.sleep(0.2)
        print ("Motor On")
        time.sleep(0.2)
        print(PUSH_MSG)
        sendPush(PUSH_MSG)
    
    
    
    URL = "Insert personal URL here" + str(distance)
    r = requests.get(URL)
    print(r)
    time.sleep(15)

