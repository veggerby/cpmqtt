import network
import time
import MQTTBroker

ssid = "frivillig"
my_password = "pirat1234"

access_point = network.WLAN(network.AP_IF)
access_point.active(True)
access_point.config(essid=ssid, password=my_password)

# while not access_point.isconnected():
#     time.sleep(1)

ip_address = access_point.ifconfig()[0]

broker = MQTTBroker.MQTTBroker(ip_address, 1883, 48, False)
broker.start()