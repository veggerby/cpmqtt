import time
import network

# Configuration for the Access Point
SSID = 'MicroPython-AP'
PASSWORD = '12345678'

sta_if = network.WLAN(network.STA_IF)

def connect_to_wifi(ssid=SSID, password=PASSWORD):
    #ap_if = network.WLAN(network.AP_IF)
    sta_if.active(True)
    sta_if.connect(ssid, password)

    print('Connecting to WiFi', end="")
    while not sta_if.isconnected():
        time.sleep(1)
        print('.', end="")

    print('connected')

def network_config():
    print('Network config:', sta_if.ifconfig())

def try_connect_to_wifi():
    if sta_if.isconnected():
        print('Already connected')
    else:
        connect_to_wifi()

    network_config()

def start_hotspot(ssid=SSID, password=PASSWORD):
    # Create an access point (AP) interface
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)
    print(f"Access Point {ssid} started with IP: {ap.ifconfig()[0]}")
