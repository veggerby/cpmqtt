from abc import ABC, abstractmethod
from MQTTClient import Client

class ProtocolHandlerInterface(ABC):
    @abstractmethod
    def handle(self, client: Client, msg: bytes):
        pass

    @abstractmethod
    def handle_connect(self, client: Client, connect_message):
        pass

    @abstractmethod
    def handle_publish(self, client: Client, publish_message):
        pass

    @abstractmethod
    def handle_subscribe(self, client: Client, subscribe_message):
        pass

    @abstractmethod
    def handle_unsubscribe(self, client: Client, unsubscribe_message):
        pass

    @abstractmethod
    def handle_pingreq(self, client: Client, pingreq_message):
        pass

    @abstractmethod
    def handle_disconnect(self, client: Client, disconnect_message):
        pass
