from MQTTLogger import Logger
from MQTTClient import Client

class ClientManager:
    logger: Logger
    clients: dict

    def __init__(self, logger = None):
        self.clients = {}
        self.logger = logger or Logger()

    def get_client(self, client_socket):
        client = self.clients[client_socket]

        if client is None:
            client = Client(client_socket, self.logger)
            self.clients[client_socket] = client

        return client

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            client = self.clients[client_socket]
            del self.clients[client_socket]
            client.close()

    def cleanup_clients(self):
        for client in list(self.clients.keys()):
            if not self.is_ready(client):
                self.logger.warning(f'Removing closed client: {client}')
                self.remove_client(client)
                client.close()
