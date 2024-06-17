from MQTTLogger import Logger

class ClientManager:
    def __init__(self, logger = None):
        self.clients = {}
        self.logger = logger or Logger()

    def add_client(self, client_socket):
        self.clients[client_socket] = {}

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            del self.clients[client_socket]

    def cleanup_clients(self):
        for client in list(self.clients.keys()):
            if not self.is_socket_open(client):
                self.logger.warning(f'Removing closed client: {client}')
                self.remove_client(client)
                client.close()