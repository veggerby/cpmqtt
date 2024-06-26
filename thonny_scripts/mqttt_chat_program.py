# sub.py
import time
from umqtt.robust import MQTTClient

# help()
import network
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.scan()                             # Scan for available access points
sta_if.connect("Signes_hytte_2.4GHz", "2744igen") # Connect to an AP
sta_if.isconnected()                      # Check for successful connection


SERVER="192.168.0.107"
ClientID = f'esp32-sub-{time.time_ns()}'
user = "allan"
password = "2744igen"
topic = "info"
modtaget = False
modtaget_besked = b'{check}'
send_besked = b'{"msg":"hello from ESP32"}'
client = MQTTClient(ClientID, SERVER, 1883, user, password)

def sub(topic, msg):
    global modtaget_besked
    print("new messages")
    if msg != modtaget_besked:
        modtaget_besked = msg
        print('received message %s on topic %s' % (msg, topic))
        pub(topic)
 
def pub(topic):
    svar = input("Skriv et svar:")
    client.publish(topic, svar, qos=0)
    print("Beskeden er sendt")

def main(server=SERVER):
    client.set_callback(sub)
    client.connect()
    print('Connected to MQTT Broker "%s"' % (server))
    client.subscribe(topic)
    while True:
        if True:
            client.wait_msg()
        else:
            client.check_msg()
            time.sleep(1)

if __name__ == "__main__":
    main()