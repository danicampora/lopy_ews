from network import WLAN
from network import LoRa
import socket
import config
import time
import json

TCP_PORT = 50140            # FIXME
TCP_IP = '10.0.10.2'        # TODO: Needs to be replaced with the actual IP

EAGAIN = const(11)

class Rider:
    def __init__(self, name, company, badge, bike):
        self.name = name
        self.company = company
        self.badge = badge
        self.bike = bike
        self.status = 'finished'
        self.speed = 0
        self.distance = 0
        self.crank = 0
        self.starttime = time.ticks_ms() / 1000


class NanoGateWay:
    def __init__(self):
        self.sock = None
        self.connected = False
        self.wlan = WLAN(mode=WLAN.STA)
        self.riders = {} # dictionary of riders
        # initialize LoRa as a Gateway (with Tx IQ inversion)
        self.lora = LoRa(tx_iq=True, rx_iq=False)

    def connect_to_wlan(self):
        if not self.wlan.isconnected():
            self.wlan.connect(ssid='Pycom_Guest', auth=(None, 'themakersofwipy'), timeout=7000)
            while not self.wlan.isconnected():
                time.sleep_ms(50)

    def connect_to_server(self):
        if self.sock:
            self.sock.close()
        self.sock = socket.socket()                 # TCP
        try:
            self.sock.connect((TCP_IP, TCP_PORT))   # TODO
            self.sock.settimeout(1)
            self.connected = True
        except Exception:
             self.sock.close() # just close the socket and try again later
             print('Socket connect failed, retrying...')
             time.sleep_ms(500)
    
    def send(self, msg):
        if self.connected and self.sock:
            try:
                self.sock.send(msg)
            except Exception:
                self.connected = False
                self.sock.close()
                self.sock = None

    def new_rider(self, name, company, badge, bike):
        rider = Rider(name, company, badge, bike)
        self.riders[bike] = rider

    def recv(self):
        if self.connected and self.sock:
            try:
                data = self.sock.recv(1024)
            except socket.timeout:
                return None
            except socket.error as e:
                if e.args[0] != EAGAIN:
                    self.connected = False
                return None
            return data

    def run(self):
        data = self.recv()
        if data:
            print(data)
            parsed_json = json.loads(data.decode('ascii'))
            print(parsed_json)
            if parsed_json['RideStatus'] == "initialized":
                self.new_rider(parsed_json['RiderName'], parsed_json['Company'], 
                               parsed_json['BadgeNumber'], parsed_json['BikeID'])
                # start the race
                packet_tx = json.dumps({'id':parsed_json['BikeID'], 'cm': 's'})
                self.lora.send(packet_tx, True)

        lora_d = self.lora.recv()
        if lora_d:
            parsed_json = json.loads(lora_d.decode('ascii'))
            print(parsed_json)
            # update the rider info (if the rider already exists)
            bike_id = parsed_json['id']
            if bike_id in self.riders:
                self.riders[bike_id].speed = parsed_json['sp']
                self.riders[bike_id].distance = parsed_json['ds']
                self.riders[bike_id].crank = parsed_json['cr']
                if parsed_json['st'] == 'i' or parsed_json['st'] == 'f':
                    self.riders[bike_id].status = 'finished'
                elif parsed_json['st'] == 'r':
                    self.riders[bike_id].status = 'counting'
                else:
                    self.riders[bike_id].status = 'started'
                # Assemble the TCP packet
                json_d = {"RiderName":self.riders[bike_id].name, "Company":self.riders[bike_id].company, "BadgeNumber":self.riders[bike_id].badge, \
                          "EventID":'EVENT_0', "RideTimestamp":self.riders[bike_id].starttime, "BikeID":bike_id, \
                          "RideStatus":self.riders[bike_id].status, "RideInfo":[{"CounterTimestamp": (time.ticks_ms() / 1000), \
                          "CrankCounter":self.riders[bike_id].crank, "WheelCounter":'WHEEL'}]}  # TODO Correct the dummy value
                json_str = json.dumps(json_d)
                self.send(json_str)
        if not self.connected:
            self.connect_to_wlan()
            self.connect_to_server()


def main():
    gateway = NanoGateWay()
    while True:
        gateway.run()
        time.sleep_ms(50)
