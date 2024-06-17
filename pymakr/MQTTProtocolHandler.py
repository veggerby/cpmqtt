import struct
from MQTTLogger import Logger
from MQTTBroker import MQTTBroker
from MQTTClient import Client, ClientSettings
from MQTTProtocolHandlerInterface import ProtocolHandlerInterface
from MQTTMessage import ConnectMessage, MQTTMessage, PublishMessage

MESSAGE_TYPE_CONNECT = 1
MESSAGE_TYPE_CONNACK = 2
MESSAGE_TYPE_PUBLISH = 3
MESSAGE_TYPE_PUBACK = 4
MESSAGE_TYPE_PUBREC = 5
MESSAGE_TYPE_PUBREL = 6
MESSAGE_TYPE_PUBCOMP = 7
MESSAGE_TYPE_SUBSCRIBE = 8
MESSAGE_TYPE_SUBACK = 9
MESSAGE_TYPE_UNSUBSCRIBE = 10
MESSAGE_TYPE_UNSUBACK = 11
MESSAGE_TYPE_PINGREQ = 12
MESSAGE_TYPE_PINGRESP = 13
MESSAGE_TYPE_DISCONNECT = 14

class ProtocolHandler(ProtocolHandlerInterface):
    SUPPORTED_PROTOCOLS = ['MQTT']

    def __init__(self, broker: MQTTBroker, logger=None):
        self.broker = broker
        self.logger = logger or Logger()

    def handle(self, client: Client, msg):
        message = MQTTMessage.create(msg)

        if (not issubclass(type(message), MQTTMessage)):
            raise ValueError('Unsupported message type')

        message.handle_message(self.broker, client)

    def handle_connect(self, client: Client, connect_message: ConnectMessage):
        try:
            client.settings = ClientSettings(
                client_id=connect_message.client_id,
                protocol_name=connect_message.protocol_name,
                protocol_version=connect_message.protocol_version,
                connect_flags=connect_message.connect_flags,
                keep_alive=connect_message.keep_alive
            )

            self.logger.debug(f'Protocol Name: {client.settings.protocol_name}')

            if client.settings.protocol_name not in ProtocolHandler.SUPPORTED_PROTOCOLS:
                raise ValueError('Unsupported protocol')

            if not client.settings.client_id:
                raise ValueError('Client ID must not be empty')

            if not connect_message.authenticate(self.broker.authenticator):
                raise ValueError('Authentication failed')

            conn_ack_flags = 0
            return_code = 0  # Connection Accepted
            conn_ack = struct.pack('>BB', 32, 2) + struct.pack('BB', conn_ack_flags, return_code)
            client.send(conn_ack)
            self.logger.debug(f'Client connected: {client.settings.client_id}')

        except ValueError as ve:
            self.logger.error(f'Error in handle_connect: {ve}')
            client.send(struct.pack('>BB', 32, 2) + struct.pack('BB', 0, 1))  # Connection Refused, unacceptable protocol version
            client.close()
        except Exception as e:
            self.logger.error(f'Error in handle_connect: {e}')
            client.send(struct.pack('>BB', 32, 2) + struct.pack('BB', 0, 2))  # Connection Refused, identifier rejected
            client.close()

    def handle_publish(self, client: Client, publish_message: PublishMessage):
        try:
            if not publish_message.topic_name:
                raise ValueError('Topic must not be empty')

            self.logger.receive(f'Received message: {publish_message.payload} on topic: {publish_message.topic_name}')
            self.broker.topic_manager.publish(publish_message.topic_name, publish_message)
            self.logger.send(f'{publish_message.payload} published to topic: {publish_message.topic_name}')

            if publish_message.qos_level == 1:  # QoS 1
                pub_ack = struct.pack('>BBH', 64, 2, publish_message.packet_id)
                client.send(pub_ack)
            elif publish_message.qos_level == 2:  # QoS 2
                raise NotImplementedError('QoS 2 not supported')

        except Exception as e:
            self.logger.error(f'Error in handle_publish: {e}')

    def handle_puback(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            self.logger.debug(f'PUBACK received for packet ID: {packet_id}')
        except Exception as e:
            self.logger.error(f'Error in handle_puback: {e}')

    def handle_pubrec(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            pubrel = struct.pack('>BBH', 0x62, 2, packet_id)
            client.send(pubrel)
            self.logger.debug(f'PUBREC received for packet ID: {packet_id}')
        except Exception as e:
            self.logger.error(f'Error in handle_pubrec: {e}')

    def handle_pubrel(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            pubcomp = struct.pack('>BBH', 0x70, 2, packet_id)
            client.send(pubcomp)
            self.logger.debug(f'PUBREL received for packet ID: {packet_id}')
        except Exception as e:
            self.logger.error(f'Error in handle_pubrel: {e}')

    def handle_pubcomp(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            self.logger.debug(f'PUBCOMP received for packet ID: {packet_id}')
        except Exception as e:
            self.logger.error(f'Error in handle_pubcomp: {e}')

    def handle_subscribe(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            topics = []

            while mqtt_message.offset < len(mqtt_message.msg):
                topic = mqtt_message.read_string()
                qos = mqtt_message.read_byte()

                if not topic:
                    raise ValueError('Topic must not be empty')

                self.broker.topic_manager.subscribe(topic, client)
                topics.append((topic, qos))

            self.logger.info(f"Client subscribed to topics: {topics}")
            sub_ack = struct.pack('>BBH', 0x90, 2 + len(topics), packet_id) + bytes([qos for topic, qos in topics])
            client.send(sub_ack)

        except Exception as e:
            self.logger.error(f'Error in handle_subscribe: {e}')

    def handle_suback(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            self.logger.debug(f'SUBACK received for packet ID: {packet_id}')
        except Exception as e:
            self.logger.error(f'Error in handle_suback: {e}')

    def handle_unsubscribe(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            topics = []

            while mqtt_message.offset < len(mqtt_message.msg):
                topic = mqtt_message.read_string()

                if not topic:
                    raise ValueError('Topic must not be empty')

                self.broker.topic_manager.unsubscribe(topic, client)
                topics.append(topic)

            self.logger.info(f"Client unsubscribed from topics: {topics}")
            unsub_ack = struct.pack('>BBH', 0xB0, 2, packet_id)
            client.send(unsub_ack)

        except Exception as e:
            self.logger.error(f'Error in handle_unsubscribe: {e}')

    def handle_unsuback(self, client: Client, mqtt_message: MQTTMessage):
        try:
            packet_id = mqtt_message.read_short()
            self.logger.debug(f'UNSUBACK received for packet ID: {packet_id}')
        except Exception as e:
            self.logger.error(f'Error in handle_unsuback: {e}')

    def handle_pingreq(self, client: Client, mqtt_message: MQTTMessage):
        try:
            client.send(b'\xD0\x00')
            self.logger.send('PINGRESP sent to client')
        except Exception as e:
            self.logger.error(f'Error sending PINGRESP: {e}')

    def handle_pingresp(self, client: Client, mqtt_message: MQTTMessage):
        self.logger.debug('PINGRESP received')

    def handle_disconnect(self, client: Client, mqtt_message: MQTTMessage):
        try:
            self.logger.info('Client disconnected')
            self.broker.client_manager.remove_client(client)
            client.close()
        except Exception as e:
            self.logger.error(f'Error handling disconnect: {e}')
