from machine import Pin
from neopixel import NeoPixel

ONBOARD_LED_PIN = 48

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)

class LED:
    pin: any
    count: any
    np: any = None

    def __init__(self, pin = ONBOARD_LED_PIN, count = 1):
        self.pin = Pin(pin)
        self.count = count
        self.np =  NeoPixel(self.pin, self.count)

    def set_color(self, number, color, apply = True):
        self.np[number] = color
        if apply:
            self.apply()

    def apply(self):
        self.np.write()

    def on(self, color = WHITE, number = 0):
        self.set_color(number, color)

    def all(self, color = WHITE):
        for i in range(self.count):
            self.set_color(i, color, False)

        self.apply()

    def off(self):
        self.all(OFF)



