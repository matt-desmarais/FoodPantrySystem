import random
import os.path
from os import path
import httplib, urllib
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import datetime as dt
import csv
import ntplib
from time import ctime
import paho.mqtt.publish as publish
 
MQTT_SERVER = "sign.local"
MQTT_PATH = "number_channel"
#########################################################################
form = "https://formstack.com/user/form?Order%20Number="
#########################################################################

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

#now = dt.datetime.now()
todayfile = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+".txt"
todayfruit = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+"fruit.txt"
fruitfile = "/home/pi/fruit.txt"
#check for fruit+date file if exists read from it set fruit
#else get todays fruit random from fruits.txt
#write fruit+date with todays fruit set fruit

now = dt.datetime.now()
logfile = "/home/pi/files/"+str(now.strftime("%Y-%m-%d"))+"logs.csv"

def sendNotification(message):
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json", urllib.urlencode({
    'Connection' : 'Keep-Alive',
    "token": "token",
    "user": "user",
    "sound": "bugle",
    "message": message,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

def random_line(fname):
    lines = open(fname).read().splitlines()
    return random.choice(lines)

def todaysFruit():
    if(path.isfile(todayfruit)):
        with open(todayfruit) as f:
            first_line = f.readline()
            fruit = str(first_line)
            sendNotification("Fruit of the day is: "+str(fruit))
    else:
        #if no fruit file then make it with a 1 inside
        f = open(todayfruit, "w")
        fruit = random_line(fruitfile)
        f.write(str(fruit))
        f.close()
        sendNotification("Fruit of the day is: "+str(fruit))
    return fruit

currentFruit = todaysFruit()

def writeNumber(phone, num):
    with open(logfile, 'a') as file:
        writer = csv.writer(file)
        writer.writerow([num, phone])

app = Flask(__name__)

@app.route("/sms", methods =['POST'])
def sms():
    phonenumber = request.form['From']
    message_body = request.form['Body']
    if("test" in message_body.lower()):
        resp = MessagingResponse()
        with open(todayfile) as f:
            first_line = f.readline()
            num = int(first_line)
        response_message = 'Hello {}, the test was successful. Next Number:{} Fruit:{}'.format(phonenumber, num, currentFruit)
        resp.message(response_message)
        return str(resp)
    if(currentFruit.lower() in message_body.lower()):
        now = dt.datetime.now()
        with open(todayfile) as f:
            first_line = f.readline()
            num = int(first_line)
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
        print("res: "+str(result))
        print("#: "+str(phonenumber))
        #check for phone number already having a number, resend message to them
        if phonenumber in result.values():
            print "found phone number"
            number = 
list(result.keys())[list(result.values()).index(phonenumber)]
            print str(number)
            response_message = 'Hello {}\nYou are number: {}'.format(phonenumber, number)+'\nPlease fill out this form.\n'+form+str(number)
            resp.message(response_message)
            return str(resp)
        else:
            #if phone not in list assign number, provide order link
            f = open(todayfile, "w")
            f.write(str(num+1))
            f.close()
            publish.single(MQTT_PATH, num+1, hostname=MQTT_SERVER)
            resp = MessagingResponse()
            response_message = 'Hello {}\nYou are number: {}'.format(phonenumber, num)+'\nPlease fill out this form.\n'+form+str(num)
            resp.message(response_message)
            now = dt.datetime.now()
            sendNotification(str(now.strftime("%m-%d %H:%M"))+"\n"+str(phonenumber)+" is number "+str(num))
            writeNumber(phonenumber, num)
            return str(resp)
    else:
        resp = MessagingResponse()
        response_message = 'Hello {}, that is not the correct word'.format(phonenumber)
        resp.message(response_message)
        return str(resp)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

