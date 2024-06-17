from MQTTLogger import Logger
from MQTTClient import Client

class ClientManager:
    logger: Logger
    clients: dict

    def __init__(self, logger = None):
        self.clients = {}
        self.logger = logger or Logger()

    def get_client(self, client_socket):
        if client_socket in self.clients:
            return self.clients[client_socket]

        client = Client(client_socket, self.logger)
        self.clients[client_socket] = client

        return client

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            client = self.clients[client_socket]
            del self.clients[client_socket]
            client.close()

    def cleanup_clients(self):
        for client_socket in list(self.clients.keys()):
            client = self.clients[client_socket]
            if not client.is_ready():
                self.logger.warning(f'Removing closed client: {client}')
                self.remove_client(client)
                client.close()
