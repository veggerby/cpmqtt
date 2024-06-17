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

import asyncio
# import uasyncio as asyncio

from MQTTProtocolHandlerInterface import ProtocolHandlerInterface

DEFAULT_TIMEOUT = 20.0
ACCEPT_TIMEOUT = 60.0
DEFAULT_PORT = 1883
SOCKET_BUFSIZE = 2048


class MQTTBrokerProtocol(asyncio.Protocol):
    def __init__(self, client_manager: ClientManager, protocol_handler: ProtocolHandlerInterface, logger: Logger):
        self.client_manager = client_manager
        self.protocol_handler = protocol_handler
        self.logger = logger

    def connection_made(self, transport):
        self.peer_name = transport.get_extra_info('peername')
        self.client = self.client_manager.get_client(self.peer_name, transport)
        self.logger.info(f'Connection from {self.peer_name}')

    def data_received(self, data):
        self.logger.info(f'Data received: {data!r}')

        self.protocol_handler.handle(self.client, data)

    def connection_lost(self, exc):
        self.logger.info(
            f'The client {self.peer_name} closed the connection {exc} {traceback.format_exc()}')
        self.client_manager.remove_client(self.peer_name)


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
        self.authenticator = authenticator or Authenticator(
            {"admin": "password"}, self.logger)
        self.protocol_handler = ProtocolHandler(
            self.authenticator, self.topic_manager, self.client_manager, self.logger)
        # self.led = neopixel.NeoPixel(machine.Pin(rgb_led), 1) if rgb_led > 0 else None

    def start(self):
        asyncio.run(self.__run(self.host, self.port))

    async def __run(self, host, port):
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_running_loop()

        server = await loop.create_server(
            lambda: MQTTBrokerProtocol(
                self.client_manager, self.protocol_handler, self.logger),
            host=host,
            port=port,
            reuse_port=True)

        async with server:
            self.logger.info(f'Starting MQTT Broker on {host}:{port}')
            await server.serve_forever()

        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        #     server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #     server_socket.bind((host, port))
        #     server_socket.listen(5)

        #     reader, writer = await asyncio.open_connection(sock=server_socket)

        #     self.logger.info(f'Starting MQTT Broker on {host}:{port}')

        #     while True:
        #         data = await reader.read(SOCKET_BUFSIZE)
        #         if not data:
        #             break

        #         self.logger.receive(f"Received message: {data.decode()!r}")

        #         client = self.client_manager.get_client(writer)

        #         self.protocol_handler.handle(client, data)

        #     await writer.wait_closed()

        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        #     server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #     server_socket.bind((self.host, self.port))
        #     server_socket.listen(5)

        #     server_socket.setblocking(False)

        #     self.logger.info(f'Starting MQTT Broker on {self.host}:{self.port}')

        #     while True:
        #         try:
        #             client_socket, address = server_socket.accept()
        #             client_socket.settimeout(ACCEPT_TIMEOUT)
        #             self.logger.info(f'New connection from {address}')
        #             threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        #         except socket.timeout:
        #             pass

        #         self.client_manager.cleanup_clients()
        #         gc.collect()

    def handle_client(self, client_socket):
        client_socket.settimeout(DEFAULT_TIMEOUT)
        buffer = b''

        while True:
            try:
                # , socket.MSG_DONTWAIT)
                msg = client_socket.recv(SOCKET_BUFSIZE)

                if not msg:
                    self.logger.error(
                        "No message received, closing connection.")
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
                self.logger.error(
                    f'Error in handle_client: {e} {traceback.format_exc()}')
                break

        client_socket.close()

    def set_led(self, color: int):
        self.logger.info(f'Setting LED color: {color}')
        # if self.rgb_led > 0:
        # self.led[0] = color
        # self.led.write()
