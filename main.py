from machine import Pin
from utime import sleep
import utime
from dht import DHT11
from lcd1602 import LCD
import secrets
import homepage

import network
import socket
import urequests
import countries
import _thread

request_queue=['local']
lcd = LCD()

lcd.write(0,0,'    Welcome    ')
lcd.write(0,1,' PiWeather Pro ')
sleep(3)
lcd.write(0,0,'               ')
sleep(0.5)
lcd.clear()

def webpage() :
    html = homepage.html
    return html

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets.ssid, secrets.password)
    t = 0
    lcd.clear()
    while not wlan.isconnected() and t<45:
        lcd.write(0,0,'connecting'+('.'*(t%5)))
        t+=1
        sleep(1)
        if t%5 == 0 :
            lcd.clear()
    ip = wlan.ifconfig()[0]
    return (ip,wlan.isconnected())

def displayLocal() :
    lcd.clear()
    dht = DHT11(Pin(0,Pin.IN, Pin.PULL_DOWN))
    lcd.write(0,0,'   Displaying  ')
    lcd.write(0,1,'  Local Weather')
    sleep(5)
    dht.measure()
    temp = dht.temperature()
    humid = dht.humidity()
    lcd.clear()
    lcd.write(0,0,"  Temp: "+str(temp)+"\xDF"+"C")
    lcd.write(0,1," Humidity: "+str(humid)+"%")
    sleep(10)

def getWeather(weather_dict):
    condition = weather_dict['condition']
    temperature = weather_dict['temperature']
    humidity = weather_dict['humidity']
    pressure = weather_dict['pressure']
    wind = weather_dict['wind']
    country = weather_dict['country']
    place = weather_dict['place']
    lcd.clear()
    lcd.write(0,0,place+','+country)
    lcd.write(0,1,condition.upper())
    sleep(6)
    lcd.clear()
    lcd.write(0,0,"  Temp: "+str(temperature)+"\xDF"+"C")
    lcd.write(0,1," Humidity: "+str(humidity)+"%")
    sleep(6)
    lcd.clear()
    lcd.write(0,0,' Wind: '+str(wind)+' kmph')
    lcd.write(0,1,'Pressure: '+str(pressure)+'mm')
    sleep(6)
    lcd.clear()


def serve(connection):
    global request_queue
    while True :
        try :
            client, addr = connection.accept()
            print("connection from ", addr, "accepted")
            request = client.recv(1024)
            req = str(request)
            if req.find('/coord') == 6 :
                sp1 = req.split(' ')
                split2 = sp1[1].split('/')
                lat = float(split2[2])
                lon = float(split2[3])
                url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={secrets.api_key}'
                weather = urequests.get(url).json()
                weather_dict = {}
                weather_dict['condition'] = weather['weather'][0]['description']
                weather_dict['temperature'] =int(weather['main']['temp'])-270
                weather_dict['humidity'] = weather['main']['humidity']
                weather_dict['pressure'] = weather['main']['pressure']
                weather_dict['wind'] = weather['wind']['speed']
                weather_dict['country'] = countries.name[weather['sys']['country']]
                weather_dict['place'] = weather['name']
                request_queue.append(weather_dict)
                print(lat,lon)
            elif req.find('/local') == 6 :
                request_queue.append('local')
            html=webpage()
            client.send(html)
            client.close()
        except OSError as e :
            client.close()
            print("connection closed")
 
def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    try : 
        connection.bind(address)
    except :
        machine.reset()
    connection.listen(1)
    print(connection,"in open socket")
    return(connection)

def displayer():
    global request_queue
    while True :
        print(request_queue)
        if len(request_queue) == 1 :
            if request_queue[0] == 'local' :
                displayLocal()
            else :
                getWeather(request_queue[0])
        else :
            if request_queue[0] == 'local' :
                displayLocal()
            else :
                getWeather(request_queue[0])
            request_queue.pop(0)

def weather_station():
    ip, connected = connect()
    if connected :
        lcd.clear()
        lcd.write(0,0,'Connect@ http://')
        lcd.write(0,1,str(ip))
        sleep(5)
        connection=open_socket(ip)
        try : 
            t = _thread.start_new_thread(displayer,())
            serve(connection)
        except :
            print('Exception created')
    else :
        lcd.clear()
        lcd.write(0,0,' WiFi Connection')
        lcd.write(0,1,'     Failed     ')
        sleep(2)
        displayLocal()
        lcd.clear()
        lcd.write(0,0,'Working on issue')
        weather_station()
try:
    weather_station()
except:
    lcd.clear()
    lcd.write(0,0,'Restarting...')
    sleep(5)
    machine.reset()
 