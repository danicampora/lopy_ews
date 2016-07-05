import socket
import json
import paho.mqtt.client as paho
import ssl
import errno, time

QOS = 0
TOPIC = "my/topic"

awshost = "A8USY1DJY36IC.iot.eu-west-1.amazonaws.com"
awsport = 8883
caPath = "aws-iot-rootCA.crt"
certPath = "ap.crt"
keyPath = "ap.key"

connflag = False

sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 50140))
sock.listen(0)
sc, addr = sock.accept()
sc.setblocking(0)

def on_connect(client, userdata, flags, rc):
    global connflag
    connflag = True
    print("Connection returned result: " + str(rc))
    print("Subscribing to topic: " + TOPIC)
    client.subscribe(TOPIC, 1)

def on_message(client, userdata, msg):
    print(str(msg.payload))

    decoded_payload = msg.payload.decode("ascii")

    parsed_json = json.loads(decoded_payload)

    # Only process messages meant for this bike (as defined by BIKE_NAME constant above
    if parsed_json['RideStatus'] == "initalised":

        starttime=time.time()

        rider_name = str(parsed_json['RiderName'])
        company = str(parsed_json['Company'])
        badge_number = str(parsed_json['BadgeNumber'])
        event_id = str(parsed_json['EventID'])
        start_timestamp = str(starttime)
        last_timestamp = starttime
        bike_id = str(parsed_json['BikeID'])

        # Send a single message indicating that the ride has started with status 'started'
        rider_status = "started"

        json_str = '{"RiderName":"'+rider_name+'","Company":"'+company+'","BadgeNumber":'+badge_number+',"EventID":"'+event_id+'","RideTimestamp":"'+start_timestamp+'","BikeID":'+bike_id+',"RideStatus":"'+rider_status+'"}'
        jsonReading = json.loads(json_str)

        print("Initialised: " + str(json_str))
        mqttc.publish(TOPIC, json.dumps(jsonReading) , qos = QOS)

        json_d = json.dumps(jsonReading)
        sc.send(bytes(json_d,'ascii'))

# Establish mqtt conncetion
mqttc = paho.Client()

mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

print("Connecting... awshost: "+awshost+" awsport: "+str(awsport)+" topic: "+TOPIC)
rc = -1
rc = mqttc.connect(awshost, awsport, keepalive=60)

print ("mqttc connect return code = "+str(rc))

while True:

    rc = mqttc.loop()

    try:
       data = sc.recv(1024)
       if not data:
          print("connection closed")
          sc.close()
          break
       else:
          decoded_payload = data.decode("ascii")
          mydata = decoded_payload.splitlines()

          i=0
          while (i<len(mydata)):
            print("Publishing: " + mydata[i])
            jsonReading = json.loads(mydata[i])
            # Workaround to avoid exponential values
            jsonReading["RideTimestamp"] = float(jsonReading["RideTimestamp"])
            mqttc.publish(TOPIC, json.dumps(jsonReading), qos = QOS)
            i=i+1

    except socket.error as e:
        if e.args[0] == errno.EWOULDBLOCK:
            print ('EWOULDBLOCK')
            time.sleep(0.1)           # short delay, no tight loops
        else:
            print (e)
            break
