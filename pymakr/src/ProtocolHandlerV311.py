from Logger import Logger
from Client import Client, ClientSettings
from ProtocolHandler import ProtocolHandler
from Messages import ConnAckMessage, ConnectMessage, DisconnectMessage, MQTTMessage, PingReqMessage, PingRespMessage, PubAckMessage, PublishMessage, SubAckMessage, SubscribeMessage, UnSubAckMessage, UnsubscribeMessage
from ClientManager import ClientManager
from Authenticator import Authenticator
from SubscriberManager import SubscriberManager

PACKET_TYPE_CONNECT = 1
PACKET_TYPE_CONNACK = 2
PACKET_TYPE_PUBLISH = 3
PACKET_TYPE_PUBACK = 4
PACKET_TYPE_PUBREC = 5
PACKET_TYPE_PUBREL = 6
PACKET_TYPE_PUBCOMP = 7
PACKET_TYPE_SUBSCRIBE = 8
PACKET_TYPE_SUBACK = 9
PACKET_TYPE_UNSUBSCRIBE = 10
PACKET_TYPE_UNSUBACK = 11
PACKET_TYPE_PINGREQ = 12
PACKET_TYPE_PINGRESP = 13
PACKET_TYPE_DISCONNECT = 14

class ProtocolHandlerV311(ProtocolHandler):
    SUPPORTED_PROTOCOLS = ['MQTT']

    def __init__(self, authenticator: Authenticator, topic_manager: SubscriberManager, client_manager: ClientManager, logger=None):
        self.authenticator = authenticator
        self.topic_manager = topic_manager
        self.client_manager = client_manager
        self.logger = logger or Logger()

    def handle(self, client: Client, msg: bytes):
        try:
            message = MQTTMessage.create(msg)

            if (not issubclass(type(message), MQTTMessage)):
                raise ValueError('Unsupported message type')

            message.handle_message(self, client)
        except Exception as e:
            self.logger.error(f'Error in handle: {e}')

    def handle_connect(self, client: Client, connect_message: ConnectMessage):
        try:
            client.settings = ClientSettings(
                connect_message.client_id,
                connect_message.protocol_name,
                connect_message.protocol_version,
                connect_message.connect_flags,
                connect_message.keep_alive)

            self.logger.debug(f'Protocol Name: {client.settings.protocol_name} {client.settings.protocol_version} from {client.settings.client_id} - {client.settings.connect_flags} - {client.settings.keep_alive}')

            if client.settings.protocol_name not in ProtocolHandlerV311.SUPPORTED_PROTOCOLS:
                raise ValueError('Unsupported protocol')

            if not client.settings.client_id:
                raise ValueError('Client ID must not be empty')

            if not connect_message.authenticate(self.authenticator):
                raise ValueError('Authentication failed')

            ConnAckMessage(0, 0).send_to(client)
            self.logger.debug(f'Client connected: {client.settings.client_id}')

        except ValueError as ve:
            self.logger.error(f'Error in handle_connect: {ve}')
            ConnAckMessage(0, 1).send_to(client) # Connection Refused, unacceptable protocol version
            client.close()
        except Exception as e:
            self.logger.error(f'Error in handle_connect: {e}')
            ConnAckMessage(0, 2).send_to(client) # Connection Refused, identifier rejected
            client.close()

    def handle_publish(self, client: Client, publish_message: PublishMessage):
        try:
            if not publish_message.topic_name:
                raise ValueError('Topic must not be empty')

            self.logger.receive(f'Received message: {publish_message.payload} on topic: {publish_message.topic_name}')
            self.topic_manager.publish(publish_message.topic_name, publish_message)
            self.logger.send(f'{publish_message.payload} published to topic: {publish_message.topic_name}')

            if publish_message.qos == 1:  # QoS 1
                PubAckMessage(publish_message).send_to(client)
            elif publish_message.qos == 2:  # QoS 2
                raise NotImplementedError('QoS 2 not supported')

        except Exception as e:
            self.logger.error(f'Error in handle_publish: {e}')

    def handle_subscribe(self, client: Client, subscribe_message: SubscribeMessage):
        try:
            self.topic_manager.subscribe(subscribe_message.topic, client)

            self.logger.info(f"Client subscribed to topics: {subscribe_message.topic}")

            SubAckMessage(subscribe_message).send_to(client)

        except Exception as e:
            self.logger.error(f'Error in handle_subscribe: {e}')

    def handle_unsubscribe(self, client: Client, unsubscribe_message: UnsubscribeMessage):
        try:
            for topic in unsubscribe_message.topics:
                self.topic_manager.unsubscribe(topic, client)
                self.logger.info(f"Client unsubscribed from topic: {topic}")

            # Send UnsubAck message back to the client
            UnSubAckMessage(unsubscribe_message).send_to(client)

        except Exception as e:
            self.logger.error(f'Error in handle_unsubscribe: {e}')

    def handle_pingreq(self, client: Client, pingreq_message: PingReqMessage):
        try:
            self.logger.info('Received PINGREQ')
            PingRespMessage(pingreq_message).send_to(client)

        except Exception as e:
            self.logger.error(f'Error sending PINGRESP: {e}')

    def handle_disconnect(self, client: Client, disconnect_message: DisconnectMessage):
        try:
            self.logger.info('Client disconnected')
            self.client_manager.remove_client(client)
            client.close()
        except Exception as e:
            self.logger.error(f'Error handling disconnect: {e}')
