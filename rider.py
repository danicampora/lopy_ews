import os
import time
import machine
import json
import config
from machine import Pin
from network import LoRa
import Adafruit_LCD as LCD

LORA_SEND_PERIOD_MS = 3000

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


def main():
    _prev_crank = 0
    _prev_wheel = 0
    _time_ms = time.ticks_ms()
    _last_sent_ms = _time_ms

    # init the crank and wheel pulse counters
    crank = PulseCounter('G10', Pin.PULL_DOWN, Pin.IRQ_RISING, 250)
    #Pin('G4', mode=Pin.IN, pull=Pin.PULL_DOWN)
    #wheel = PulseCounter('G5', Pin.PULL_DOWN, Pin.IRQ_RISING, 200)

    _lora = LoRa()

    # Raspberry Pi LCD pin configuration:
    lcd_rs        = 'G11'
    lcd_en        = 'G12'
    lcd_d4        = 'G15'
    lcd_d5        = 'G16'
    lcd_d6        = 'G13'
    lcd_d7        = 'G28'

    lcd_columns   = 16
    lcd_rows      = 1

    lcd = LCD.CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
    lcd.message('C={:4d}'.format(_prev_crank) + '\nW={:4d}'.format(_prev_wheel))

    _start_delay_ms = ((machine.rng() % 30) * 100) + time.ticks_ms()

    while True:
        if (_prev_crank != crank.counter):
            _prev_crank = crank.counter // 2    # Need to divide by 2 as pulses are duplicated
            lcd.home()
            lcd.message('C={:4d}'.format(_prev_crank) + '\nW={:4d}'.format(_prev_wheel))

        #if (_prev_wheel != wheel.counter):
        #    _prev_wheel = wheel.counter
        #    #lcd.clear()
        #    lcd.message('C={:4d}'.format(_prev_crank) + '\nW={:4d}'.format(_prev_wheel))
        
        _time_ms = time.ticks_ms()
        if _time_ms < _start_delay_ms:
            pass
        elif _time_ms > _last_sent_ms + LORA_SEND_PERIOD_MS:
            _last_sent_ms = _time_ms
            _packet = json.dumps({"id": config.id, "c": _prev_crank, "w": _prev_wheel})
            print(_packet + ' {}'.format(_last_sent_ms))
            _lora.send(_packet, False)

        time.sleep_ms(50)
