import socket
import traceback
from MQTTLogger import Logger

class ClientSettings:
    client_id: any
    protocol_name: any
    protocol_version: any
    connect_flags: any
    keep_alive: any

    def __init__(self, client_id, protocol_name, protocol_version, connect_flags, keep_alive):
        self.client_id = client_id
        self.protocol_name = protocol_name
        self.protocol_version = protocol_version
        self.connect_flags = connect_flags
        self.keep_alive = keep_alive

class Client:
    client_socket: socket.socket
    settings: ClientSettings

    def __init__(self, client_socket: socket.socket, logger = None):
        self.client_socket = client_socket
        self.logger = logger or Logger()

    def is_ready(self):
        try:
            self.client_socket.send(b'')
            return True
        except OSError:
            return False

    def send(self, msg):
        try:
            self.client_socket.send(msg)
        except OSError as e:
            self.logger.error(f'Error sending message to client: {e}, {traceback.format_exc()}')

    def close(self):
        self.logger.info('Closing client connection')

        try:
            self.client_socket.close()
        except OSError as e:
            self.logger.error(f'Error closing client connection: {e}, {traceback.format_exc()}')
