#!/usr/bin/env python3
import argparse
import signal
import sys
import time
import logging
import RPi.GPIO as GPIO
import datetime as dt
from os import path
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics
from PIL import Image
import ntplib
from time import ctime
from rpi_rf import RFDevice

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
#options.cols = 64
options.chain_length = 4
options.parallel = 1
options.hardware_mapping = 'adafruit-hat-pwm'  # If you have an Adafruit 
HAT: 'adafruit-hat'
options.drop_privileges = 0
options.daemon = 0
options.pixel_mapper_config = 'U-mapper'

matrix = RGBMatrix(options = options)
max_brightness = matrix.brightness
offscreen_canvas = matrix.CreateFrameCanvas()
font = graphics.Font()
font.LoadFont("/home/pi/FoodPantrySystem/NumberSign/fonts/newoldfontx2new.bdf")
font2 = graphics.Font()
font2.LoadFont("/home/pi/FoodPantrySystem/NumberSign/fonts/10x20.bdf")
pos = 0
textColor = graphics.Color(255, 0, 0)
image_file = "/home/pi/FoodPantrySystem/NumberSign/logo.png"
image = Image.open(image_file)

image.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)

def displayNext():
    global offscreen_canvas, pos, my_text
    pos = 0
    offscreen_canvas.Clear()
    graphics.DrawText(offscreen_canvas, font2, 12, 45, textColor, "Next")
    #offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    graphics.DrawText(offscreen_canvas, font2, 2, 64, textColor, "Number")
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

def displayNumber(number):
    global offscreen_canvas, pos, my_text
    if(number < 10):
        pos = 16
    elif(number >= 10):
        pos = -5
    offscreen_canvas.Clear()
    graphics.DrawText(offscreen_canvas, font, pos, 64, textColor, 
str(number))
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

def transition():
    matrix.Fill(0, 0, 0)
    offscreen_canvas.Clear()
    displayNext()
    matrix.SetImage(image.convert('RGB'))
    while(matrix.brightness > 1):
        matrix.brightness -= 5
        offscreen_canvas.Clear()
        matrix.SetImage(image.convert('RGB'))
        print("IN LOOP")
        time.sleep(.1)
    matrix.brightness = max_brightness



MQTT_SERVER = "numbermachine.local"
MQTT_PATH = "number_channel"

rfdevice = None
c = ntplib.NTPClient()
response = c.request('pool.ntp.org', version=3)
ctime(response.tx_time)
now = dt.datetime.strptime(ctime(response.tx_time), "%a %b %d %H:%M:%S 
%Y")
print(str(now)+"NOW")
todayfile = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+".txt"
todayMax = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+"Max.txt"
lastnumber = None
maxNum = 1
MQTT_SERVER2 = "localhost"
MQTT_PATH2 = "number_channel"
 
# The callback for when the client receives a CONNACK response from the 
server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
 
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH2)
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    global maxNum, lastnumber
    maxNum = int(msg.payload)
    print(maxNum)
    f = open(todayMax, "w")
    f.write(str(maxNum))
    f.close()
    # more callbacks, etc
 
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
 
client.connect_async(MQTT_SERVER2, 1883, 60)
 
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a manual interface.
client.loop_start()

GPIO.setmode(GPIO.BCM)
BuzzerPin = 14
GPIO.setup(BuzzerPin, GPIO.OUT)
GPIO.output(BuzzerPin, GPIO.HIGH)

#read from todays file or create it.
def todaysFile():
    global lastnumber
    #if todays file exists load from it
    if(path.isfile(todayfile)):
        with open(todayfile) as f:
            first_line = f.readline()
            lastnumber = int(first_line)
            displayNumber(lastnumber)
            print("LAST: "+str(lastnumber))
    if(path.isfile(todayMax)):
        with open(todayMax) as f:
            global maxNum
            first_line = f.readline()
            maxNum = int(first_line)
            print("MAX: "+str(maxNum))
    else:
        #if no number file then make it with a 0 inside
        f = open(todayfile, "w")
        f.write("0")
        f.close()
        displayNumber(0)

#read from todays file or create it.
def todaysMax():
    #if todays file exists load from it
    if(path.isfile(todayMax)):
        with open(todayMax) as f:
            first_line = f.readline()
            number = int(first_line)
            maxNum = number

#turn buzzer on
def on():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BuzzerPin, GPIO.OUT)
    GPIO.output(BuzzerPin, GPIO.LOW)

#turn buzzer off
def off():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BuzzerPin, GPIO.OUT)
    GPIO.output(BuzzerPin, GPIO.HIGH)

#beep sequence
def beep(x):
    on()
    time.sleep(x)
    off()
    time.sleep(x)

def exithandler(signal, frame):
    rfdevice.cleanup()
    sys.exit(0)

def nextNumber():
    with open(todayfile) as f:
       first_line = f.readline()
       num = int(first_line)+1
    print("NUM "+str(num))
    print("MAX "+str(maxNum))
    if(num < maxNum):
        print("Called number: "+str(num))
        f = open(todayfile, "w")
        f.write(str(num))
        f.close()
        transition()
        displayNumber(num)
        publish.single(MQTT_PATH, num, qos=1, hostname=MQTT_SERVER)
    else:
        beep(.25)
        beep(.25)
        beep(.25)

#load last number called
todaysFile()
todaysMax()

logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s', )
parser = argparse.ArgumentParser(description='Receives a decimal code via a 433/315MHz GPIO device')
parser.add_argument('-g', dest='gpio', type=int, default=15, help="GPIO pin (Default: 25)")
args = parser.parse_args()
signal.signal(signal.SIGINT, exithandler)
rfdevice = RFDevice(args.gpio)
rfdevice.enable_rx()
timestamp = None
logging.info("Listening for codes on GPIO " + str(args.gpio))

num = lastnumber
while True:
    if rfdevice.rx_code_timestamp != timestamp:
        timestamp = rfdevice.rx_code_timestamp
        print(str(rfdevice.rx_code))
        if((str(rfdevice.rx_code) == "12345678") or (str(rfdevice.rx_code) == "87654321")):
            rfdevice.cleanup()
            rfdevice.rx_code = None
            print("Detected")
            beep(1)
            nextNumber()
            time.sleep(1)
            rfdevice = RFDevice(args.gpio)
            rfdevice.enable_rx()

    time.sleep(0.01)
rfdevice.cleanup()
