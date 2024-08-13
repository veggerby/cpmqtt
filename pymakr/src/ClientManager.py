from Logger import Logger
from Client import Client

class ClientManager:
    logger: Logger
    clients: dict

    def __init__(self, logger = None):
        self.clients = {}
        self.logger = logger or Logger()

    def get_client(self, client_name: str) -> Client:
        if client_name in self.clients:
            return self.clients[client_name]

        return None

    def add_client(self, client: Client):
        if client.client_name in self.clients:
            raise ValueError(f'Client {client.client_name} already exists')

        self.clients[client.client_name] = client

    def remove_client(self, client: Client):
        if client.client_name in self.clients:
            del self.clients[client.client_name]
            client.close()

    def cleanup_clients(self):
        try:
            for client_name in list(self.clients.keys()):
                client = self.clients[client_name]
                if not client.is_ready():
                    self.logger.warning(f'Removing closed client: {client}')
                    self.remove_client(client)
                    client.close()
        except Exception as e:
            self.logger.error(f'Error cleaning up clients: {e}')
