from abc import ABC, abstractmethod
from MQTTClient import Client

class ProtocolHandlerInterface(ABC):
    @abstractmethod
    def handle(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_connect(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_publish(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_puback(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_pubrec(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_pubrel(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_pubcomp(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_subscribe(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_suback(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_unsubscribe(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_unsuback(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_pingreq(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_pingresp(self, client: Client, msg):
        pass

    @abstractmethod
    def handle_disconnect(self, client: Client, msg):
        pass
