#!/usr/bin/env python3
import asyncio
import sys
from Authenticator import Authenticator
from Broker import Broker
from Client import Client, ClientSettings
from Logger import Logger

DEFAULT_PORT = 1883

class MQTTClient(Client):
    def __init__(self, client_name: str, client_settings: ClientSettings, transport: asyncio.BaseTransport, logger: Logger = None):
        super().__init__(client_name, client_settings, logger)
        self.transport = transport

    def is_ready(self):
        try:
            self.transport.write(b'')
            return True
        except OSError:
            return False

    def send(self, msg: bytes):
        try:
            self.transport.write(msg)
        except OSError as e:
            self.logger.error(f'Error sending message to client: {e}')

    def close(self):
        self.logger.info('Closing client connection')

        try:
            self.transport.close()
        except OSError as e:
            self.logger.error(f'Error closing client connection: {e}')

class MQTTBrokerProtocol(asyncio.Protocol):
    client: MQTTClient = None

    def __init__(self, broker: Broker, logger: Logger):
        self.broker = broker
        self.logger = logger

    def connection_made(self, transport):
        peer_name = transport.get_extra_info('peername')

        client = self.broker.client_manager.get_client(peer_name)

        if client is None:
            client = MQTTClient(peer_name, None, transport, self.logger)
            self.broker.client_manager.add_client(client)

        self.logger.info(f'Connection from {peer_name}')

        self.client = client

    def data_received(self, data):
        if not self.client:
            raise ValueError('Client not initialized')

        self.logger.info(f'Data received: {data!r}')

        self.broker.protocol_handler.handle(self.client, data)

    def connection_lost(self, exc):
        self.logger.info(
            f'The client {self.client.client_name} closed the connection {exc}')
        self.broker.client_manager.remove_client(self.client)

class MQTTServer:
    def __init__(self, broker: Broker, host: str = '0.0.0.0', port: int = DEFAULT_PORT, logger: Logger = None):
        self.broker = broker
        self.host = host
        self.port = port
        self.logger = logger or Logger(True)

    async def start_server(self):
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_running_loop()

        server = await loop.create_server(
            lambda: MQTTBrokerProtocol(self.broker, self.logger),
            host=self.host,
            port=self.port,
            reuse_port=True)

        async with server:
            self.logger.info(f'Starting MQTT Broker on {self.host}:{self.port}')
            await server.serve_forever()


def main():
    host = '0.0.0.0'
    port = 1883

    authenticator: Authenticator = None
    if sys.argv and len(sys.argv) > 1 and sys.argv[1] == 'auth':
        # Define the user database for authentication
        user_db = {
            "admin": "password",  # Replace with your desired username and password
            "user": "userpass"
        }

        authenticator = Authenticator(user_db)

    # Initialize the broker
    broker = Broker(authenticator=authenticator)

    server = MQTTServer(broker, host, port)
    asyncio.run(server.start_server())

if __name__ == "__main__":
    main()
