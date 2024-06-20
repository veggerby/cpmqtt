import time
import network

sta_if = network.WLAN(network.STA_IF)

def connect_to_wifi():
    #ap_if = network.WLAN(network.AP_IF)
    sta_if.active(True)
    sta_if.connect('PET_Vogn_1', 'fkvgsppfb0207')

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
