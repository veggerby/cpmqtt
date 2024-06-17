import gc
from platform import machine
# import neopixel
import socket
import threading
import traceback
from MQTTLogger import Logger
from MQTTAuthenticator import Authenticator
from MQTTClientManager import ClientManager
from MQTTProtocolHandler import ProtocolHandler
from MQTTTopicManager import TopicManager
from MQTTClient import Client

DEFAULT_TIMEOUT = 20.0
ACCEPT_TIMEOUT = 60.0
DEFAULT_PORT = 1883
SOCKET_BUFSIZE = 2048

class MQTTBroker:

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
        self.logger = logger or Logger(True)
        self.client_manager = ClientManager(self.logger)
        self.topic_manager = TopicManager(self.logger)
        self.authenticator = authenticator or Authenticator({"admin": "password"}, self.logger)
        self.protocol_handler = ProtocolHandler(self.authenticator, self.topic_manager, self.client_manager, self.logger)
        # self.led = neopixel.NeoPixel(machine.Pin(rgb_led), 1) if rgb_led > 0 else None

    def start(self):
        # server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # server_socket.bind((self.host, self.port))
        # server_socket.listen(5)

        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        server_socket = socket.socket()
        server_socket.bind(addr)
        server_socket.listen(5)

        self.logger.info(f'Starting MQTT Broker on {self.host}:{self.port}')

        while True:
            try:
                client_socket, address = server_socket.accept()
                client_socket.settimeout(ACCEPT_TIMEOUT)
                self.logger.info(f'New connection from {address}')
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except socket.timeout:
                pass

            self.client_manager.cleanup_clients()
            gc.collect()

    def handle_client(self, client_socket):
        client_socket.settimeout(DEFAULT_TIMEOUT)
        buffer = b''

        while True:
            try:
                msg = client_socket.recv(SOCKET_BUFSIZE)

                if not msg:
                    self.logger.error("No message received, closing connection.")
                    self.remove_client(client_socket)
                    break

                buffer += msg
                while len(buffer) >= 2:
                    remaining_length, multiplier = 0, 1
                    for i in range(1, len(buffer)):
                        byte = buffer[i]
                        remaining_length += (byte & 0x7f) * multiplier
                        if (byte & 0x80) == 0:
                            break
                        multiplier *= 128

                    total_length = 1 + i + remaining_length
                    if len(buffer) < total_length:
                        break

                    msg = buffer[:total_length]
                    buffer = buffer[total_length:]

                self.logger.receive(f"Received message: {msg}")

                client = self.client_manager.get_client(client_socket)

                self.protocol_handler.handle(client, msg)
            except Exception as e:
                self.logger.error(f'Error in handle_client: {e} {traceback.format_exc()}')
                break

        client_socket.close()

    def set_led(self, color: int):
        self.logger.info(f'Setting LED color: {color}')
        # if self.rgb_led > 0:
            # self.led[0] = color
            # self.led.write()
