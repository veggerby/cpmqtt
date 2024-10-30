import time
from umqtt.robust import MQTTClient
from machine import Pin
from neopixel import NeoPixel
import wifi
import random

NAVN = 'skriv_dit_navn_her'

## ESP32 CP network
SSID = 'frivillig'
PASSWORD = 'test1234'
MQTT_BROKER = '192.168.100.129'
MQTT_PORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None

CLIENT_ID = f'esp32-{NAVN}-{time.time_ns()}'

INFO_TOPIC = 'info'
LED_TOPIC = f'led/{NAVN}'

wifi.disable()
wifi.try_connect_to_wifi(SSID, PASSWORD)

client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USERNAME, password=MQTT_PASSWORD)

# Konfiguration af NeoPixel LED
pin = 48  # GPIO 48
num_leds = 1
np = NeoPixel(Pin(pin), num_leds)

def skift_farve(farve):
    print(f'Skifter LED til {farve}')
    color = None
    if (farve == 'red'):
        color = (255, 0, 0)
    elif (farve == 'green'):
        color = (0, 255, 0)
    elif (farve == 'blue'):
        color = (0, 0, 255)
    elif (farve == 'random'):
        color = (random.randrange(180), random.randrange(180), random.randrange(180))
    elif (farve == 'off'):
        color = (0, 0, 0)
    else:
        print(f'Ukendt farve {farve}')
        return

    np[0] = color
    np.write()

def subscribe(topic, msg):
    topic_name = topic.decode('utf-8')
    message = msg.decode('utf-8')
    print(f'Received message {message} on {topic_name}')
    if topic_name == LED_TOPIC:
        skift_farve(message)

client.connect()
client.set_callback(subscribe)

print(f'Connected to MQTT Broker: {MQTT_BROKER}')

client.subscribe(INFO_TOPIC)
client.subscribe(LED_TOPIC)

while True:
    client.check_msg()
