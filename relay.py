""" The object to actually control the lights
    To be updated to actually, you know, control the lights??"""
from machine import Pin

class Relay(object):
    def __init__(self, pin=None, mode=None):
        self.pin = pin
        self.mode = mode
        self.on = False
        if mode == "relay":
            self.Pin = Pin (self.pin, Pin.OUT)
        else:
            self.Pin = None

    def react(self):
        if self.Pin:
            self.Pin.value(int(self.on))
        else:
            print(f"Relay on = {self.on}")

    def turn_on(self):
        self.on = True
        self.react()

    def turn_off(self):
        self.on = False
        self.react()
