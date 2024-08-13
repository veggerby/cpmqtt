import uasyncio as asyncio

from Broker import Broker
from Messages import MQTTMessage
from Client import Client
from Logger import Logger
from Authenticator import Authenticator

DEFAULT_PORT = 1883
SOCKET_BUFSIZE = 2048

class uMQTTClient(Client):
    def __init__(self, client_name: str, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter, logger = None):
        self.client_name = client_name
        self.client_reader = client_reader
        self.client_writer = client_writer
        self.logger = logger or Logger()

    def is_ready(self):
        try:
            self.client_writer.write(b'')
            return True
        except OSError:
            return False

    def send(self, msg: bytes):
        try:
            self.client_writer.write(msg)
        except OSError as e:
            self.logger.error(f'Error sending message to client: {e}')

    def close(self):
        self.logger.info('Closing client connection')

        try:
            self.client_writer.close()
        except OSError as e:
            self.logger.error(f'Error closing client connection: {e}')

class uMQTTServer:
    def __init__(self, host='0.0.0.0', port=DEFAULT_PORT, broker: Broker=None, logger: Logger=None):
        self.logger = logger or Logger()
        self.broker = broker or Broker(logger=self.logger)
        self.host = host
        self.port = port

    async def handle_client(self, client_reader, client_writer):
        client_name = client_writer.get_extra_info('peername')

        self.logger.info(f'New client connected {client_name}')

        client = self.broker.client_manager.get_client(client_name)

        if client is None:
            client = uMQTTClient(client_name, client_reader, client_writer, self.broker.logger)
            self.broker.client_manager.add_client(client)

        try:
            while True:
                data = await client_reader.read(SOCKET_BUFSIZE)

                if not data or len(data) == 0:
                    break

                self.broker.protocol_handler.handle(client, data)
        except Exception as e:
            self.logger.error(f'Error handling client: {e}')
            raise e
        finally:
            self.logger.info(f'Client disconnected {client_name}')
            client_writer.close()
            await client_writer.wait_closed()
            self.broker.client_manager.remove_client(client)

    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port, backlog=10)
        await server.wait_closed()

def start_local():
    logger = Logger()
    try:
        host = '0.0.0.0'
        port = 1883

        # Define the user database for authentication
        user_db = {
            "admin": "password",  # Replace with your desired username and password
            "user": "userpass"
        }

        logger.info(f'Starting server listening on {host}:{port}')

        # Initialize the broker
        broker = Broker(authenticator=Authenticator(user_db), logger=logger)

        server = uMQTTServer(host, port, broker, logger=logger)
        asyncio.run(server.start_server())
    except Exception as e:
        logger.error(f'Error starting server: {e}')
        raise e
    finally:
        asyncio.new_event_loop()  # Clear uasyncio stored state
