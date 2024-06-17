import socket
from MQTTLogger import Logger


class ClientSettings:
    client_id: any
    protocol_name: any
    protocol_version: any
    connect_flags: any
    keep_alive: any

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
            self.logger.error(f'Error sending message to client: {e}')

    def close(self):
        self.logger.info('Closing client connection')

        try:
            self.client_socket.close()
        except OSError as e:
            self.logger.error(f'Error closing client connection: {e}')
