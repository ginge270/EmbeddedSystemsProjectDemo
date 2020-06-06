import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from datetime import datetime
import time
import csv
import requests

#Subscribe channel
MQTT_SERVER = "192.168.3.7"
MQTT_PATH = "medication_check_channel"

#Publish channel
MQTT_SERVER2 = "192.168.3.129"
MQTT_PATH2 = "medication_response_channel"

dateTimeNow = datetime.now()
d_string = dateTimeNow.strftime("%Y-%m-%d")
t_string = dateTimeNow.strftime("%H:%M:%S")

#function to append data to csv file
def appendFile(file_name, dict_of_elem, field_names):
    #Open file in append mode
    with open(file_name, 'a+', newline='') as f:
        thewriter = csv.DictWriter(f, fieldnames= field_names)
        thewriter.writerow(dict_of_elem)

#function to check access status
def logCheck(file_name, col1, col2):
    with open(file_name,'r', newline='') as f:
        thereader = csv.DictReader(f)
        status = False
        while status == False:
            for row in thereader:
                if row[col1] == d_string and row[col2] == '1':
                    status = True
            print(status)
            return(status)

#function to publish reply messages
def sendResponse(status):
    if status == True:
        publish.single(MQTT_PATH2, "Medication already accessed", hostname=MQTT_SERVER2)
        
    elif status == False:
        publish.single(MQTT_PATH2, "Medication access authorised", hostname=MQTT_SERVER2)

#function to check if successful medication attempt has been made
def accessCheck():
    timeNow = datetime.datetime.now()
    if timeNow >= 15:
        if client.on_message != True:
            #sends request to trigger IFTTT
            requests.post('https://maker.ifttt.com/trigger/Medication__Not_Accessed/with/key/b1oUXXOgcwFSkg6M6Vvfra')
                


# The callback for when the client receives a connect response from the server.
def on_connect(client, userdata, flags, rc):
    print("MQTT Connected with code "+ str(rc))

    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    dateTimeNow = datetime.now()
    d_string = dateTimeNow.strftime("%Y-%m-%d")
    t_string = dateTimeNow.strftime("%H:%M:%S")
    msg.payload = msg.payload.decode("utf-8")
    print("date and time: ", d_string," ",t_string, " Message Received: ", str(msg.payload))
    field_Names = ['date','time','authentication']
    msg = str(msg.payload)
          
    #appends record of attempt and send IFTTT email notification    
    if msg == "Declined Authentication attempt":
        row_dict = {'date': d_string,'time': t_string,'authentication': '0' }
        appendFile('medicationlog2.csv', row_dict, field_Names)
        #sends request to trigger IFTTT
        requests.post('https://maker.ifttt.com/trigger/Unauthorised_Access_Attempt/with/key/b1oUXXOgcwFSkg6M6Vvfra')
        #print("Done")
    
    #appends record of attempt and send IFTTT email notification  
    elif msg == "Authenticated access attempt":
        status = logCheck('medicationlog2.csv', 'date','authentication')
        sendResponse(status)
        row_dict = {'date': d_string,'time': t_string,'authentication': '1' }
        appendFile('medicationlog2.csv', row_dict, field_Names)
        
        try:
            if status == True:
                #sends request to trigger IFTTT
                requests.post('https://maker.ifttt.com/trigger/Multiple_Medication_Attempts/with/key/b1oUXXOgcwFSkg6M6Vvfra')
                #print("Done")
            elif status == False:
                #sends request to trigger IFTTT
                requests.post('https://maker.ifttt.com/trigger/Authorised_Medication_Access/with/key/b1oUXXOgcwFSkg6M6Vvfra')
                #print("Done")
        
        #error handling
        except RuntimeError():
            print("Runtime Error has occured")
        except OSError():
            print("OS Error has occured")
    
            
        return(True)
    
    



while True:
    try:
    
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_SERVER, 1883, 60)


        client.loop_forever()
    
        accessCheck()
        
    except RuntimeError():
        print("Runtime Error has occured")
