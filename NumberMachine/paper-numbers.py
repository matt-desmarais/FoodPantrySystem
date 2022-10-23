#!/usr/bin/python
import time
import RPi.GPIO as GPIO
import datetime as dt
from escpos import printer
import http.client, urllib
import os.path
from os import path
import ntplib
from time import ctime
import paho.mqtt.publish as publish
from datetime import timedelta

MQTT_SERVER = "sign.local"
MQTT_PATH = "number_channel"

c = ntplib.NTPClient()
response = c.request('pool.ntp.org', version=3)
ctime(response.tx_time)
ntpnow = dt.datetime.strptime(ctime(response.tx_time), "%a %b %d %H:%M:%S %Y")
print(ntpnow)
print(ntpnow.date())
now = dt.datetime.now()
print(now)
while(ntpnow.date() != now.date()):
    print("looping")
    now = dt.datetime.now()
    time.sleep(.5)
#setup printer
p = printer.Usb(0x0456,0x0808,0,0x82,0x03)
#set vars
number = 1
count = 0
starttime=0
#now = dt.datetime.now()
todayfile = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+".txt"
todayfruit = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+"fruit.txt"
# Use BCM based pin numbering
GPIO.setmode(GPIO.BCM)

def todaysFruit():
    if(path.isfile(todayfruit)):
        with open(todayfruit) as f:
            first_line = f.readline()
            fruit = str(first_line)
        return fruit

#read from todays file or create it.
def todaysFile():
    #if todays file exists load from it
    if(path.isfile(todayfile)):
        with open(todayfile) as f:
            first_line = f.readline()
            number = int(first_line)
    else:
        #if no number file then make it with a 1 inside
        f = open(todayfile, "w")
        f.write("1")
        f.close()

#send push notification
def sendNotification(message):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json", urllib.parse.urlencode({
    'Connection' : 'Keep-Alive',
    "token": "token",
    "user": "user",
    "sound": "bugle",
    "message": message,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

#what to print at startup
def printStart():
    with open(todayfruit) as f:
        first_line = f.readline()
        fruit = str(first_line)
    with open(todayfile) as f:
       first_line = f.readline()
       num = int(first_line)
    try:
        publish.single(MQTT_PATH, num, hostname=MQTT_SERVER)
    except:
        print("No mqtt connection")
    p.set(align='center', font='a', width=2, height=2, density=9, 
invert=False, smooth=False, flip=False)
    p.text("Sandwich Food Pantry\n\n")
    now = dt.datetime.now()
    p.text(str(now.strftime("%m-%d %H:%M")+"\n"))
    p.text("Starting number:"+str(num)+"\n")
    p.set(align='center', font='a', width=6, height=6, density=9, 
invert=False, smooth=False, flip=False)
    p.text("Phone Number\n")
    p.set(align='center', font='a', width=2, height=2, density=9, 
invert=False, smooth=False, flip=False)
    p.text("todays fruit is:\n")
    p.set(align='center', font='a', width=6, height=6, density=9, 
invert=False, smooth=False, flip=False)
    p.text(str(fruit))
    p.cut()

#print number and send notification about the number being given out
def printNumber():
    now = dt.datetime.now()
    with open(todayfile) as f:
       first_line = f.readline()
       num = int(first_line)
    print("Gave out paper number: "+str(num))
    f = open(todayfile, "w")
    f.write(str(num+1))
    f.close()
    p.set(align='center', font='a', width=2, height=2, density=9, 
invert=False, smooth=False, flip=False)
    p.text("Sandwich Food Pantry\n\n")
    p.set(align='center', font='a', width=1, height=1, density=9, 
invert=False, smooth=False, flip=False)
    p.text("Keep an eye out for your number\n\n")
    p.text(str(now.strftime("%m-%d %H:%M")+"\n"))
    p.text("Your number is\n")
    p.set(align='center', font='a', width=6, height=6, density=9, invert=False, smooth=False, flip=False)
    p.text(str(num))
    p.cut()
    sendNotification((str(now.strftime("%m-%d %H:%M")+"\nJust gave out number: ")+str(num)))
    try:
        publish.single(MQTT_PATH, num+1, qos=1, hostname=MQTT_SERVER)
    except:
        print("No mqtt connection")


#read distance from sensor return distance in cm
def ReadDistance(pin):
   starttime=0
   endtime=0
   GPIO.setup(pin, GPIO.OUT)
   GPIO.output(pin, 0)
   time.sleep(0.000002)
   #send trigger signal
   GPIO.output(pin, 1)
   time.sleep(0.000005)
   GPIO.output(pin, 0)
   GPIO.setup(pin, GPIO.IN)
   looptime=time.time()
   while GPIO.input(pin)==0 and (time.time() - looptime) <= .5:
      starttime=time.time()
   looptime=time.time()
   while GPIO.input(pin)==1 and (time.time() - looptime) <= .5:
      endtime=time.time()
   duration=endtime-starttime
   # Distance is defined as time/2 (there and back) * speed of sound 34000 cm/s 
   distance=duration*34000/2
   return distance

#set todays file
todaysFile()
#print start status
printStart()

while True:
    distance = ReadDistance(14)
    if(distance <= 40):
        count = count + 1
    else:
        count = 0
    if(count >= 6):
        printNumber()
        count = 0
        time.sleep(5)
    time.sleep(.4)

