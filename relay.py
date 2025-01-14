""" The object to actually control the lights
    To be updated to actually, you know, control the lights??"""
from machine import Pin
from picozero import LED

class Relay(object):
    def __init__(self, pin=None, mode=None):
        self.pin = pin
        self.mode = mode
        self.on = False
        if mode == "relay":
            self.hardware = LED(self.pin)
        else:
            self.hardware = None
        print(self.hardware, self.mode, self.pin)

    def react(self):
        if self.hardware:
            if self.on:
                self.hardware.on()
            else:
                self.hardware.off()       
        print(f"Relay on = {self.on}")

    def set_state(self, alive=True):
        self.on = alive
        self.react()

    def turn_on(self):
        self.on = True
        self.react()

    def turn_off(self):
        self.on = False
        self.react()
