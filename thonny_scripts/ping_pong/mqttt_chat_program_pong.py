# sub.py
import time
from umqtt.robust import MQTTClient

# help()
import network
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.scan()                             # Scan for available access points
sta_if.connect("frivillig", "") # Connect to an AP
#sta_if.isconnected()                      # Check for successful connection

print("Connected to wifi")

while not sta_if.isconnected():
    time.sleep(1)
    print(".")


SERVER="192.168.4.1"
ClientID = f'esp32-sub-{time.time_ns()}'
topic_send = "pong"
topic_modtag = "ping"
modtaget = False
modtaget_besked = b'{check}'
send_besked = b'{"msg":"hello from ESP32"}'
client = MQTTClient(ClientID, SERVER, 1883)#, user, password)
nummer = 0

def sub(topic, msg):
    global modtaget_besked
    print("new messages")
    if msg != modtaget_besked:
        modtaget_besked = msg
        print('received message %s on topic %s' % (msg, topic_modtag))
        time.sleep(1)
        pub()
 
def pub():
    global topic_send
    global nummer
    svar = f"{topic_send} #{nummer}"
    nummer = nummer + 1
    client.publish(topic_send, svar, qos=0)
    print("Beskeden er sendt")

def main(server=SERVER):
    client.set_callback(sub)
    client.connect(0)
    print('Connected to MQTT Broker "%s"' % (server))
    client.subscribe(topic_modtag)
    while True:
        if True:
            client.wait_msg()
        else:
            client.check_msg()
            time.sleep(1)

if __name__ == "__main__":
    main()