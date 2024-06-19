from Broker import Broker
import uasyncio
from Messages import MQTTMessage
import traceback
from Client import Client
from Logger import Logger
from Authenticator import Authenticator
from ClientManager import ClientManager
from ProtocolHandlerV311 import ProtocolHandlerV311
from SubscriberManager import SubscriberManager

DEFAULT_PORT = 1883
SOCKET_BUFSIZE = 2048

class uMQTTClient:
    def __init__(self, client_name: str, client_reader: uasyncio.StreamReader, client_writer: uasyncio.StreamWriter, logger = None):
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
            self.logger.error(f'Error sending message to client: {e}, {traceback.format_exc()}')

    def close(self):
        self.logger.info('Closing client connection')

        try:
            self.client_writer.close()
        except OSError as e:
            self.logger.error(f'Error closing client connection: {e}, {traceback.format_exc()}')

class uMQTTServer:
    def __init__(self, broker: Broker, host='0.0.0.0', port=DEFAULT_PORT):
        self.broker = broker
        self.host = host
        self.port = port

    async def handle_client(self, client_reader, client_writer):
        client_name = client_writer.get_extra_info('peername')
        client = self.broker.client_manager.get_client(client_name)

        if client is None:
            client = uMQTTClient(client_name, client_reader, client_writer, self.broker.logger)
            self.broker.client_manager.add_client(client)
        try:
            while True:
                data = await client_reader.read(SOCKET_BUFSIZE)
                if not data:
                    break
                message = MQTTMessage.create(data)
                await message.handle_message(self.broker.protocol_handler, client)
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            client_writer.close()
            await client_writer.wait_closed()

    async def start_server(self):
        server = await uasyncio.start_server(self.handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()

async def main():
    host = '0.0.0.0'
    port = 1883

    # Define the user database for authentication
    user_db = {
        "admin": "password",  # Replace with your desired username and password
        "user": "userpass"
    }

    # Initialize the broker
    broker = Broker(authenticator=Authenticator(user_db))

    server = uMQTTServer(broker, host, port)
    uasyncio.run(server.start_server())

if __name__ == "__main__":
    main()
