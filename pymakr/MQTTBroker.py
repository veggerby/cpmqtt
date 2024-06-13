import MQTTLogger
import ClientManager
import TopicManager
import ProtocolHandler
import Authenticator
import neopixel
import machine
import socket
import threading
import gc

class MQTTBroker:
    DEFAULT_TIMEOUT = 20.0
    ACCEPT_TIMEOUT = 60.0
    DEFAULT_PORT = 1883

    def __init__(self, host='0.0.0.0', port=DEFAULT_PORT, rgb_led=4, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.rgb_led = rgb_led
        self.client_manager = ClientManager()
        self.topic_manager = TopicManager()
        self.authenticator = Authenticator({"admin": "password"})
        self.led = neopixel.NeoPixel(machine.Pin(rgb_led), 1) if rgb_led > 0 else None
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        MQTTLogger.info(f'Starting MQTT Broker on {self.host}:{self.port}', self.debug)

        while True:
            self.sock.settimeout(self.ACCEPT_TIMEOUT)
            try:
                client, address = self.sock.accept()
                client.settimeout(self.DEFAULT_TIMEOUT)
                MQTTLogger.info(f'New connection from {address}', self.debug)
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except socket.timeout:
                pass
            self.client_manager.cleanup_clients()
            gc.collect()

    def handle_client(self, client):
        while True:
            try:
                msg = client.recv(2048)
                if not msg:
                    break
                MQTTLogger.receive(f"Received message: {msg}", self.debug)
                msg_type = msg[0] >> 4

                if msg_type == 1:
                    ProtocolHandler.handle_connect(client, msg, self)
                elif msg_type == 3:
                    ProtocolHandler.handle_publish(client, msg, self)
                elif msg_type == 8:
                    ProtocolHandler.handle_subscribe(client, msg, self)
                elif msg_type == 10:
                    ProtocolHandler.handle_unsubscribe(client, msg, self)
                elif msg_type == 12:
                    ProtocolHandler.send_pingresp(client, self)
                elif msg_type == 14:
                    ProtocolHandler.handle_disconnect(client, self)
                    break
                else:
                    MQTTLogger.error(f"Unknown message type: {msg_type}", self.debug)
            except Exception as e:
                MQTTLogger.error(f'Error in handle_client: {e}', self.debug)
                break

        client.close()

    def set_led(self, color):
        if self.rgb_led > 0:
            self.led[0] = color
            self.led.write()

if __name__ == "__main__":
    broker = MQTTBroker(host='0.0.0.0', port=1883, rgb_led=4, debug=True)
    broker.start()
