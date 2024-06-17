import gc
from platform import machine
# import neopixel
import socket
import threading
from MQTTLogger import Logger
from MQTTAuthenticator import Authenticator
from MQTTClientManager import ClientManager
from MQTTProtocolHandler import ProtocolHandler
from MQTTTopicManager import TopicManager
from MQTTClient import Client

class MQTTBroker:
    DEFAULT_TIMEOUT = 20.0
    ACCEPT_TIMEOUT = 60.0
    DEFAULT_PORT = 1883
    SOCKET_BUFSIZE = 2048

    host: str
    port: int
    rgb_led: int
    logger: Logger
    client_manager: ClientManager
    topic_manager: TopicManager
    protocol_handler: ProtocolHandler
    authenticator: Authenticator

    def __init__(self, host: str = '0.0.0.0', port: int = DEFAULT_PORT, rgb_led: int = -1, authenticator: Authenticator = None, logger: Logger = None):
        self.host = host
        self.port = port
        self.rgb_led = rgb_led
        self.logger = logger or Logger()
        self.client_manager = ClientManager(self.logger)
        self.topic_manager = TopicManager(self.logger)
        self.authenticator = authenticator or Authenticator({"admin": "password"}, self.logger)
        self.protocol_handler = ProtocolHandler(self, self.logger)
        # self.led = neopixel.NeoPixel(machine.Pin(rgb_led), 1) if rgb_led > 0 else None
        self.server_socket = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.logger.info(f'Starting MQTT Broker on {self.host}:{self.port}')

        while True:
            self.server_socket.settimeout(self.ACCEPT_TIMEOUT)

            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(self.DEFAULT_TIMEOUT)
                self.logger.info(f'New connection from {address}')
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except socket.timeout:
                pass

            self.client_manager.cleanup_clients()
            gc.collect()

    def handle_client(self, client_socket):
        while True:
            try:
                client = self.client_manager.get_client(client_socket)

                msg = client_socket.recv(self.SOCKET_BUFSIZE)

                if not msg:
                    break

                self.logger.receive(f"Received message: {msg}")

                self.protocol_handler.handle(client, msg)
            except Exception as e:
                self.logger.error(f'Error in handle_client: {e}')
                break

        client_socket.close()

    def set_led(self, color: int):
        self.logger.info(f'Setting LED color: {color}')
        # if self.rgb_led > 0:
            # self.led[0] = color
            # self.led.write()
