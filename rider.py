import time
import machine
import json
import config
from machine import Pin
from network import LoRa
import Adafruit_LCD as LCD

LORA_SEND_PERIOD_MS = const(2500)

# Bike Constants (note that DISTANCE_TARGET is in meters)
COUNTDOWN_LENGTH = 3
RIDE_COMPLETE_DELAY = 5
BIKE_NAME = "1"
DISTANCE_TARGET = 500
DISTANCE_PER_REVOLUTION = 2.1362 

class PulseCounter:
    def __init__(self, pin, pull, trigger, debounce_ms):
        self._pin = Pin(pin, mode=Pin.IN, pull=pull)
        self._debounce_ms = debounce_ms
        self._last_count_ms = time.ticks_ms()
        self._irq = self._pin.irq(trigger=trigger, handler=self._handler)
        self.counter = 0

    def _handler(self, pin):
        time_ms = time.ticks_ms()
        if (time_ms - self._last_count_ms > self._debounce_ms):
            self.counter += 1
            self._last_count_ms = time_ms


class Rider:
    def __init__(self, lcd):
        global DISTANCE_TARGET
        self.distance_travelled = 0
        self.last_distance = 0
        self.speed = 0
        self.distance_remaining = DISTANCE_TARGET
        self.starttime = 0
        self.lcd = lcd

    def countdown(self):
        global COUNTDOWN_LENGTH
        global DISTANCE_TARGET
        count_down = COUNTDOWN_LENGTH
        self.lcd.clear()
        while(count_down > 0):
            print("Ready in " + str(count_down))
            self.lcd.home()
            self.lcd.message("Ready in\n {:2d}".format(count_down))
            count_down -= 1
            time.sleep_ms(1000)
        print("GO! GO! GO!")
        self.distance_remaining = DISTANCE_TARGET
        self.lcd.clear()
        self.lcd.message("GO! GO! \nGO!")
        self.starttime = time.ticks_ms() / 1000

    def ride(self, crank):
        global DISTANCE_TARGET
        if self.distance_travelled <= DISTANCE_TARGET:
            # Pull the crank values and calculate the wheel rotations 
            crank_counter_local = str(crank.counter // 2)
            wheel_counter_local_calc = (crank.counter // 2) * 2.8 
            wheel_counter_local = str(wheel_counter_local_calc)
                
            # Workout distance travelled from previous loop
            last_distance_travelled = self.distance_travelled
            calc_current_timestamp = time.ticks_ms() / 1000
            current_timestamp = str(time.ticks_ms() / 1000)

            # Workout the Distance Travelled and covert from meters per second to miles per hour
            self.distance_travelled = (wheel_counter_local_calc * DISTANCE_PER_REVOLUTION) * 2.2237
            distance_loop = self.distance_travelled - last_distance_travelled
            self.speed = (self.distance_travelled / (calc_current_timestamp - self.starttime)) 
            self.distance_remaining = DISTANCE_TARGET - self.distance_travelled
            print("Wheel Counter: " + str(wheel_counter_local_calc) + " | Average Speed (miles per hour): " + str(self.speed) + " | Distance Remaining (meters): " + str(self.distance_remaining)) 

            # Write out speed and distance left to LCD display 
            self.lcd.clear()
            self.lcd.message("AMPH:" + str(int(self.speed)) + "\nMtrs:" + str(int(self.distance_remaining)))

            # this is sent by the gateway
            #json_str = '{"RiderName":"'+rider_name+'","Company":"'+company+'","BadgeNumber":'+badge_number+',"EventID":"'+event_id+'","RideTimestamp":'+start_timestamp+',"BikeID":'+bike_id+',"RideStatus":"'
            #+rider_status+'","RideInfo":[{"CounterTimestamp":'+current_timestamp+',"CrankCounter":'+crank_counter_local+',"WheelCounter":'+wheel_counter_local+'}]}'
            #json_reading = json.loads(json_str)     
            # print(json_reading)
            # TODO: Publish json_reading to TOPIC, QOS
            
            return False
        else:
            return True

    def distance(self):
        return self.distance_remaining

    def avg_speed(self):
        return self.speed

    def finish(self):
        global RIDE_COMPLETE_DELAY
        count_down = RIDE_COMPLETE_DELAY
        print("Ride Complete!")
        self.lcd.clear()
        self.lcd.message("Ride Com\nplete!")
        while(count_down > 0):
          count_down -= 1
          time.sleep_ms(1000)


def main():
    time_ms = time.ticks_ms()
    last_sent_ms = time_ms
    state = 'IDLE'   # States are: 'IDLE', 'RUNNING', 'FINISHED'

    Pin('G4', mode=Pin.IN, pull=Pin.PULL_DOWN)
    crank = PulseCounter('G5', Pin.PULL_DOWN, Pin.IRQ_RISING, 250)

    # initialize LoRa as a node (with Rx IQ inversion)
    lora = LoRa(tx_iq=False, rx_iq=True)

    # LCD pin configuration:
    lcd_rs        = 'G11'
    lcd_en        = 'G12'
    lcd_d4        = 'G15'
    lcd_d5        = 'G16'
    lcd_d6        = 'G13'
    lcd_d7        = 'G28'

    lcd_columns   = 16
    lcd_rows      = 1

    lcd = LCD.CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

    rider = Rider(lcd)

    print("Ready for first rider.")
    lcd.clear()
    lcd.message("Ready fo\nr first rider.")

    while True:
        if state == 'IDLE':
            packet_rx = lora.recv()
            if packet_rx:
                parsed_json = json.loads(packet_rx.decode('ascii'))
                cmd = parsed_json['cm']
                id = parsed_json['id']
                if cmd == 's' and id == config.id:
                    print('Going to running state')
                    start_delay_ms = ((machine.rng() % 30) * 100) + time.ticks_ms()
                    # send 's' (started) state over LoRa
                    packet_tx = json.dumps({'id': config.id, 'cr':0, 'ds':int(rider.distance()), 'sp':int(rider.avg_speed()), 'st':'s'})
                    lora.send(packet_tx, True)
                    rider.countdown()
                    # change to the running state and notify the gateway
                    state = 'RUNNING'
                    packet_tx = json.dumps({'id': config.id, 'cr':0, 'ds':int(rider.distance()), 'sp':int(rider.avg_speed()), 'st':'r'})
                    lora.send(packet_tx, True)
            else:
                time.sleep_ms(50)

        elif state == 'RUNNING':
            if rider.ride(crank):
                print('Going to finished state')
                state = 'FINISHED'
                packet_tx = json.dumps({'id': config.id, 'cr':crank.counter, 'ds':int(rider.distance()), 'sp':int(rider.avg_speed()), 'st':'f'})
                lora.send(packet_tx, True)
            time_ms = time.ticks_ms()
            if time_ms < start_delay_ms:
                pass
            elif time_ms > last_sent_ms + LORA_SEND_PERIOD_MS:
                last_sent_ms = time_ms
                packet_tx = json.dumps({'id':config.id, 'cr':crank.counter, 'ds':int(rider.distance()), 'sp':int(rider.avg_speed()), 'st':'r'})
                print(packet_tx + ' {}'.format(last_sent_ms))
                lora.send(packet_tx, True)
            else:
                print('attempt to receive lora')
                packet_rx = lora.recv()
                if packet_rx:
                    print(packet_rx)
                    parsed_json = json.loads(packet_rx.decode('ascii'))
                    # check the packet received and process the commands

            time.sleep(1.0 - (((time.ticks_ms() / 1000) - rider.starttime) % 1.0))

        else:
            print('finishing ride')
            rider.finish()
            # change to the running state and notify the gateway
            state = 'IDLE'
            packet_tx = json.dumps({'id': config.id, 'cr':crank.counter, 'ds':int(rider.distance()), 'sp':int(rider.avg_speed()), 'st':'i'})
            lora.send(packet_tx, True)
