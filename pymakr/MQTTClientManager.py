from asyncio import BaseTransport
from MQTTLogger import Logger
from MQTTClient import Client

class ClientManager:
    logger: Logger
    clients: dict

    def __init__(self, logger = None):
        self.clients = {}
        self.logger = logger or Logger()

    def get_client(self, client_name: str, transport: BaseTransport):
        if client_name in self.clients:
            return self.clients[client_name]

        client = Client(client_name, transport, self.logger)
        self.clients[client_name] = client

        return client

    def remove_client(self, client_name):
        if client_name in self.clients:
            client = self.clients[client_name]
            del self.clients[client_name]
            client.close()

    def cleanup_clients(self):
        for client_name in list(self.clients.keys()):
            client = self.clients[client_name]
            if not client.is_ready():
                self.logger.warning(f'Removing closed client: {client}')
                self.remove_client(client)
                client.close()
