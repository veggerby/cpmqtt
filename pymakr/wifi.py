import time
import network

# Configuration for the Access Point
SSID = 'frivillig'
PASSWORD = 'test1234'

sta_if = network.WLAN(network.STA_IF)

def connect_to_wifi(ssid=SSID, password=PASSWORD, retries=5):
    #ap_if = network.WLAN(network.AP_IF)
    sta_if.active(True)
    sta_if.scan()
    sta_if.connect(ssid, password)

    print(f'Connecting to WiFi {ssid}', end="")
    retry = retries
    while not sta_if.isconnected() and retry > 0:
        time.sleep(1)
        print('.', end="")
        retry -= 1

    return sta_if.isconnected()

def network_config():
    print('Network config:', sta_if.ifconfig())

def try_connect_to_wifi(ssid=SSID, password=PASSWORD):
    retry = 10
    if sta_if.isconnected():
        print('Already connected')
    else:
        while not connect_to_wifi(ssid, password) and retry > 0:
            disable()
            time.sleep(1)
            retry -= 1

    network_config()

def disable():
    sta_if.active(False)
    print('disconnected')

def start_hotspot(ssid=SSID, password=PASSWORD):
    # Create an access point (AP) interface
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    print(f"Access Point {ssid} started with IP: {ap.ifconfig()[0]}")



