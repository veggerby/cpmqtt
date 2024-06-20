from Messages import MQTTMessage
from Client import Client
from Logger import Logger
from Authenticator import Authenticator
from ClientManager import ClientManager
from ProtocolHandlerV311 import ProtocolHandlerV311
from SubscriberManager import SubscriberManager

class Broker:
    logger: Logger
    client_manager: ClientManager
    topic_manager: SubscriberManager
    protocol_handler: ProtocolHandlerV311
    authenticator: Authenticator

    def __init__(self, authenticator: Authenticator = None, logger: Logger = None):
        self.logger = logger or Logger(True)
        self.client_manager = ClientManager(self.logger)
        self.topic_manager = SubscriberManager(self.logger)
        self.authenticator = authenticator or Authenticator({"admin": "password"}, self.logger)
        self.protocol_handler = ProtocolHandlerV311(self.authenticator, self.topic_manager, self.client_manager, self.logger)

    async def handle(self, client: Client, message: MQTTMessage):
        self.logger.info(f'Message from {client}')
        await message.handle_message(self.protocol_handler, client)
