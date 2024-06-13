import MQTTLogger

class ClientManager:
    def __init__(self):
        self.clients = {}

    def add_client(self, client_socket):
        self.clients[client_socket] = {}

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            del self.clients[client_socket]

    def get_client_by_id(self, client_id):
        return self.clients.get(client_id)

    def cleanup_clients(self):
        for client in list(self.clients.keys()):
            if not self.is_socket_open(client):
                MQTTLogger.warning(f'Removing closed client: {client}', True)
                self.remove_client(client)
                client.close()

    @staticmethod
    def is_socket_open(sock):
        try:
            sock.send(b'')
            return True
        except OSError:
            return False
