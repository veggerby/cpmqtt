import wifi
import uMQTTServer
from machine import Pin
from neopixel import NeoPixel
import random


AP = False

NAVN = f"JohnDoe{random.randint(1, 100)}"

# Configuration for WIFI
SSID = 'frivillig' if not AP else f'esp32-{NAVN}'
PASSWORD = 'test1234'

# Konfiguration af NeoPixel LED
pin = 48  # GPIO 48
num_leds = 1
np = NeoPixel(Pin(pin), num_leds)

RED = (127, 0, 0)
YELLOW = (127, 127, 0)
GREEN = (0, 127, 0)
OFF = (0, 0, 0)

def status_led(color = OFF):
    np[0] = color
    np.write()
    #print(f"Led: {color}")

#wifi.scan_wifi()

status_led(YELLOW)

try:
    if AP:
        wifi.start_hotspot(SSID, PASSWORD)
    else:
        wifi.try_connect_to_wifi(SSID, PASSWORD)
    status_led(GREEN)
    uMQTTServer.start_local()
except:
    status_led(RED)

status_led()
