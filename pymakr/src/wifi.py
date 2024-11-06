import time
import network

# Configuration for the Access Point
SSID = 'frivillig'
PASSWORD = 'test1234'
DEFAULT_CHANNEL = 10
DEFAULT_COUNTRY = 'DK'

sta_if = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)

def scan_wifi():
    sta_if.active(True)
    list = sta_if.scan()
    print('Available networks:')
    for ssid in list:
        print(ssid[0].decode())
    sta_if.active(False)

def connect_to_wifi(ssid=SSID, password=PASSWORD, retries=20):
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
    ap.active(False)

def start_hotspot(ssid=SSID, password=PASSWORD, channel=DEFAULT_CHANNEL, country=DEFAULT_COUNTRY, retries=10):
    # Create an access point (AP) interface
    disable()

    network.country(DEFAULT_COUNTRY)
    ap.active(True)
    ap.config(essid=ssid, key=password, channel=channel)

    while not ap.active() and retries > 0:
        time.sleep(1)
        print('.', end="")
        retries -= 1

    print(f"Access Point {ssid} started with IP: {ap.ifconfig()[0]}")



