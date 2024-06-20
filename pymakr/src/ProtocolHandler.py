from Client import Client

class ProtocolHandler:
    def handle(self, client: Client, msg: bytes):
        pass

    def handle_connect(self, client: Client, connect_message):
        pass

    def handle_publish(self, client: Client, publish_message):
        pass

    def handle_subscribe(self, client: Client, subscribe_message):
        pass

    def handle_unsubscribe(self, client: Client, unsubscribe_message):
        pass

    def handle_pingreq(self, client: Client, pingreq_message):
        pass

    def handle_disconnect(self, client: Client, disconnect_message):
        pass
