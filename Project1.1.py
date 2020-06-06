import serial, time, sys
from time import sleep
from datetime import datetime
import RPi.GPIO as GPIO
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import mfrc522
import requests

#Set the GPIO naming convention
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Create an object of the class MFRC522
MIFAREReader = mfrc522.MFRC522()

#create variables
green_LED = 4
red_LED = 3
blue_LED = 24
servoPin = 17
authCode = [[81,1,63,46],[187,148,125,131]]


dateTimeNow = datetime.now()
dt_string = dateTimeNow.strftime("%Y-%m-%d %H:%M:%S")

#setup GPIO pins as output
GPIO.setup(green_LED, GPIO.OUT)
GPIO.setup(red_LED, GPIO.OUT)
GPIO.setup(blue_LED, GPIO.OUT)
GPIO.setup(servoPin, GPIO.OUT)

#setup PWM on servoPin at 50Hz
pwm = GPIO.PWM(servoPin, 50)
pwm.start(0)

#Publish Channel
MQTT_SERVER = "192.168.3.7"
MQTT_PATH = "medication_check_channel"

#Subscribe channel
MQTT_SERVER2 = "192.168.3.129"
MQTT_PATH2 = "medication_response_channel"


# Welcome message
print("Looking for cards")
print("Press Ctrl-C to stop.")

#Ensures LEDs are powered off
GPIO.output(blue_LED, False) 
GPIO.output(green_LED, False) 
GPIO.output(red_LED, False) 

#the callback for when a client receives a connect response from the server
def on_connect2(client, userdate, flags, rc):
    print("MQTT Connected with code "+ str(rc))
    
    client.subscribe(MQTT_PATH2)

#the callback for when a PUBLISH message is received from the server
def on_message2(client, userdata, msg):
    msg.payload = msg.payload.decode("utf-8")
    msg = str(msg.payload)
    #print(msg)
    
    #grants access to medication box and turns on green LED
    if msg == "Medication access authorised":
        GPIO.output(red_LED, False)
        GPIO.output(blue_LED, False)
        GPIO.output(green_LED, True)
        setAngle(90)
        sleep(10)
        setAngle(0)
        GPIO.output(green_LED, False)
        
    #declines access to medication box and turns on red LED
    elif msg == "Medication already accessed":
        GPIO.output(green_LED, False)
        GPIO.output(blue_LED, False)
        GPIO.output(red_LED, True)
        sleep(20)
        GPIO.output(red_LED, False)
        

#function to set angle of servo motor    
def setAngle(angle):
    #variable equal to angle divided by 18+2
    duty = angle / 18 + 2
    #turns the pin on for input
    GPIO.output(servoPin, True)
    #changes duty cycle to match what was calculated
    pwm.ChangeDutyCycle(duty)
    sleep(1)
    #turn off the pin
    GPIO.output(servoPin, False)
    #changes the duty back to 0
    pwm.ChangeDutyCycle(0)
    
client = mqtt.Client()
client.on_connect = on_connect2
client.on_message = on_message2
client.connect(MQTT_SERVER2, 1883, 60)

client.loop_start()
    

# This loop checks for chips. If one is near it will get the UID

try:
  
    while True:
        
        try:
    
   

            # Scan for cards
            (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

            # Get the UID of the card
            (status,uid) = MIFAREReader.MFRC522_Anticoll()

            # If we have the UID, continue
            if status == MIFAREReader.MI_OK:
                # Print UID
                print("Card UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
      
                i = 0
                length = len(authCode)
                authStatus = 0
                print(uid)
      
                # for loop to authenticate card number against authCode array of authorised cards
                for i in range(length):
                    #print(authCode[i])
                    if uid[0] == authCode[i][0]  and uid[1]== authCode[i][1] and uid[2] == authCode[i][2] and uid[3] == authCode[i][3]:
                        print("Authenticated")
                        authStatus = 1
            
        
        
        
                #if RFID not verified, declines access, turns on red LED and sends MQTT message to record
                if authStatus == 0:
                    #print("Authenticaton Declined")
                    GPIO.output(green_LED, False)
                    GPIO.output(blue_LED, False)
                    GPIO.output(red_LED, True)
                    publish.single(MQTT_PATH, "Declined Authentication attempt", hostname=MQTT_SERVER)
                    sleep(5)
                    GPIO.output(red_LED, False)
                  
            
                #if RFID verified, turns on blue LED, sends MQTT message to record and further validation    
                if authStatus == 1:
                    GPIO.output(red_LED, False)
                    GPIO.output(green_LED, False)
                    GPIO.output(blue_LED, True)
                    publish.single(MQTT_PATH, "Authenticated access attempt", hostname=MQTT_SERVER)
            
 
            
        
                time.sleep(2)


        except RuntimeError:
            print("Runtime Error has occured")  

except KeyboardInterrupt:
    client.loop_stop()
    pwm.stop()
    GPIO.cleanup()
