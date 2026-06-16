# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Import standard python modules.
import board
import adafruit_bmp280
import sys
import time
import random
import os
import http.client as httplib
import urllib.parse
import csv
from datetime import datetime
# Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C() # uses board.SCL and board.SDA
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

# change this to match the location's pressure (hPa) at sea level
bmp280.sea_level_pressure = 1011.53

# This example uses the MQTTClient instead of the REST client
from Adafruit_IO import MQTTClient
import RPi.GPIO as GPIO
from Adafruit_IO import Client
aio = Client('username', 'aio key')
#dhtDevice = adafruit_dht.DHT11(board.D21)
ADAFRUIT_IO_KEY = "aio key"

ADAFRUIT_IO_USERNAME = "username"

# Set to the ID of the feed to subscribe to for updates.
FEED_ID = 'led'
l1 = 17
l2 = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(l1,GPIO.OUT)
GPIO.setup(l2,GPIO.OUT)

#sensor = adafruit_dht.DHT11
FEED_ID = 'buzzer'
b1 = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(b1,GPIO.OUT)

## pasted in this class definition from project 1
# class LEDPair:
#     def __init__(self, yellow_pin: int, green_pin: int):
#         self.yellow_pin = yellow_pin
#         self.green_pin = green_pin
#         GPIO.setup(self.yellow_pin, GPIO.OUT, initial=GPIO.LOW)
#         GPIO.setup(self.green_pin, GPIO.OUT, initial=GPIO.LOW)
# 
#     def set_status(self, authorized: bool):
#         GPIO.output(self.green_pin, GPIO.HIGH if authorized else GPIO.LOW)
#         GPIO.output(self.yellow_pin, GPIO.LOW if authorized else GPIO.HIGH)
# 
#     def off(self):
#         GPIO.output(self.yellow_pin, GPIO.LOW)
#         GPIO.output(self.green_pin, GPIO.LOW)
 

# called when we're connected to adafruit mqtt server
def connected(client):
    """Connected function will be called when the client is connected to
    Adafruit IO.This is a good place to subscribe to feed changes. The client
    parameter passed to this function is the Adafruit IO MQTT client so you
    can make calls against it easily.
    """
    # Subscribe to changes on a feed named Counter.
    print('Subscribing to Feed {0}'.format(FEED_ID))
    client.subscribe("led1")
    client.subscribe("led2")
    client.subscribe("buzzer")
    print('Waiting for feed data...')

#this function will be automatically called, if we're disconnected from adafruit mqtt server
def disconnected(client):
    """Disconnected function will be called when the client disconnects."""
    sys.exit(1)

# this function will be called whenever there is a new data to the feeds to which we've subscribed
def message(client, feed_id, payload):
    """Message function will be called when a subscribed feed has a new value.
    The feed_id parameter identifies the feed, and the payload parameter has
    the new value.
    """
    print('Feed {0} received new value: {1}'.format(feed_id, payload))
    print("Actual payload is ",payload)
    if feed_id == 'led1':
        if payload == 'ON':
            print("turn on LED 1 here")
            GPIO.output(l1,True)
        if payload == 'OFF':
            print("turn Off LED 1 here")
            GPIO.output(l1,False)
    if feed_id == 'led2':
        if payload == 'ON':
            print("turn on LED 2 here")
            GPIO.output(l2,True)
        if payload == 'OFF':
            print("turn Off LED 2 here")
            GPIO.output(l2,False)
    if feed_id == 'buzzer':
        if payload == 'ON':
            print("turn on BUZZER here")
            GPIO.output(b1,True)
        if payload == 'OFF':
            print("turn Off BUZZER here")
            GPIO.output(b1,False)


#setup pushover API
app_key = "Put personal key here"
user_key = "Put personal key here"

#Message to be sent via Pushover
PUSH_MSG = "Weather alert!"

# This function sends the push message using Pushover.

# Create an MQTT client instance.
client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

# Setup the callback functions defined above.
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message

# Connect to the Adafruit IO server.
client.connect()

# The first option is to run a thread in the background so you can continue
# doing things in your program, to do so use below line
client.loop_background()
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
# Alternatively, you can simply block your program for waiting for incoming stream of
# data from subscription and the message function will take care of stuffs
#client.loop_blocking()

file = open("/home/pi/Project2/data_log.csv", "a")
if os.stat("/home/pi/Project2/data_log.csv").st_size == 0:
        file.write("Time,Temperature(C),Pressure(hPa),Altitude(m)\n")

while True:
    print("\nTemperature: %0.1f C" % bmp280.temperature)
    print("Pressure: %0.1f hPa" % bmp280.pressure)
    print("Altitude = %0.2f meters" % bmp280.altitude)

    aio.send('temperature', bmp280.temperature)
    aio.send('atmospheric-pressure', bmp280.pressure)
    aio.send('altitude', bmp280.altitude)
    
    now = datetime.now().replace(microsecond=0)
    file.write(f"{now},{bmp280.temperature:.2f},{bmp280.pressure:.2f},{bmp280.altitude:.2f}\n")
    file.flush()
    
    if bmp280.altitude > 421:
        print(PUSH_MSG)
        sendPush(PUSH_MSG)
        
    if bmp280.temperature > 0 or bmp280.temperature > 35:
        print(PUSH_MSG)
        sendPush(PUSH_MSG)
        
    if bmp280.pressure < 950:
        print(PUSH_MSG)
        sendPush(PUSH_MSG)
    
    
    time.sleep(15)

#     try:
#    # setup an indefinite loop
#        while True:
#           # print and push message and log to file
#           
# 
#           # do you want a time delay in between alarms?
#           time.sleep(DELAY)

