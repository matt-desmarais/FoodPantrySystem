from twilio.rest import Client
import paho.mqtt.client as mqtt
import csv
import datetime as dt
import httplib, urllib
from os import path
import ntplib
from time import ctime

MQTT_SERVER = "localhost"
MQTT_PATH = "number_channel"

#Twilio credentials
account_sid = 'sid'
auth_token = 'token'
messaging_sid = 'message sid'
client = Client(account_sid, auth_token)
 

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

logfile = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+"logs.csv"
todayfile = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+".txt"

def sendNotification(message):
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.urlencode({
        'Connection' : 'Keep-Alive',
        "token": "token",
        "user": "user",
        "sound": "climb",
        "message": message,
      }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()


def sendSMS(phone, num):
    client = Client(account_sid, auth_token)
    print "sending message"
    message = client.messages \
        .create(
             body='hey, '+str(phone)+', now calling your number!',
             messaging_service_sid=messaging_sid,
             to=phone
         )
    print(message.sid)
    print "sent message"
    now = dt.datetime.now()
    sendNotification(str(phone)+" \nnumber "+str(num)+" was just texted \n"+str(now.strftime("%m-%d %H:%M")))

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
 
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    currentNumber = str(msg.payload)
    print("before reader")
    # more callbacks, etc
    if(path.isfile(logfile)):
        reader = csv.reader(open(logfile))
        result = {}
        print("after reader")
        for row in reader:
            key = row[0]
            if key in result:
                # implement your duplicate row handling here
                pass
            result[key] = row[1]
        data = ""
    else:
        result = {}
    if currentNumber in result:
        print "found phone number"
        data = result.get(currentNumber)
        print data
        data = result[currentNumber]
        sendSMS(data, currentNumber)
    else:
        now = dt.datetime.now()
        print "paper number"
        sendNotification("Number "+str(currentNumber)+" is next with a paper number\n"+str(now.strftime("%m-%d %H:%M")))
 
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
 
client.connect(MQTT_SERVER, 1883, 60)
 
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
