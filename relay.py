""" The object to actually control the lights
    To be updated to actually, you know, control the lights??"""


class Relay(object):
    def __init__(self, pin=None, mode=None):
        self.pin = pin
        self.mode = mode
        self.on = False

    def turn_on(self):
        self.on = True

    def turn_off(self):
        self.on = False
