from network import WLAN
from network import LoRa
import socket
#import config
import time

UDP_RECV_PORT = 50140
UDP_SEND_PORT = 50141
UDP_IP = '192.168.8.7'      # TODO: Needs to be replaced with the actual IP

class NanoGateWay:
    def __init__(self):
        self.wlan = WLAN(mode=WLAN.STA)
        self.connect_to_wlan()
        self.sock = None
        self.connected = False
        self.lora = LoRa()

    def connect_to_wlan(self):
        self.wlan.connect(ssid='Smart421_Guest', auth=(None, 'Marvall0us'), timeout=7000)
        while not self.wlan.isconnected():
            time.sleep_ms(50)

    def connect_to_rpi(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.sock.bind(('', UDP_RECV_PORT))
    
    def send(self, msg):
        if self.connected and self.sock:
            try:
                self.sock.sendto(msg, (UDP_IP, UDP_SEND_PORT))
            except Exception:
                self.connected = False
                self.sock.close()
                self.sock = None

    def run(self):
        lora_p = self.lora.recv()
        if lora_p:
            self.send(lora_p)
        if not self.connected:
            self.connect_to_wlan()
            self.connect_to_rpi()
        
def main():
    gateway = NanoGateWay()
    while True:
        gateway.run()
        time.sleep_ms(50)

