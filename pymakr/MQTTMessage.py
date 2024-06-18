import struct
import abc

from MQTTAuthenticator import Authenticator
from MQTTClient import Client
from MQTTProtocolHandlerInterface import ProtocolHandlerInterface

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

class MQTTMessage(abc.ABC):
    msg: bytes

    @staticmethod
    def create(msg) -> 'MQTTMessage':
        message_type, _, _ = MQTTMessage.__read_header(msg)
        if message_type == MESSAGE_TYPE_CONNECT:
            return ConnectMessage(msg)
        elif message_type == MESSAGE_TYPE_CONNACK:
            return ConnAckMessage(msg)
        elif message_type == MESSAGE_TYPE_PUBLISH:
            return PublishMessage(msg)
        elif message_type == MESSAGE_TYPE_PUBACK:
            return PubAckMessage(msg)
        elif message_type == MESSAGE_TYPE_PUBREC:
            return PubRecMessage(msg)
        elif message_type == MESSAGE_TYPE_PUBREL:
            return PubRelMessage(msg)
        elif message_type == MESSAGE_TYPE_PUBCOMP:
            return PubCompMessage(msg)
        elif message_type == MESSAGE_TYPE_SUBSCRIBE:
            return SubscribeMessage(msg)
        elif message_type == MESSAGE_TYPE_SUBACK:
            return SubAckMessage(msg)
        elif message_type == MESSAGE_TYPE_UNSUBSCRIBE:
            return UnsubscribeMessage(msg)
        elif message_type == MESSAGE_TYPE_UNSUBACK:
            return UnsubAckMessage(msg)
        elif message_type == MESSAGE_TYPE_PINGREQ:
            return PingReqMessage(msg)
        elif message_type == MESSAGE_TYPE_PINGRESP:
            return PingRespMessage(msg)
        elif message_type == MESSAGE_TYPE_DISCONNECT:
            return DisconnectMessage(msg)
        else:
            raise ValueError(f'Unsupported message type: {message_type}')

    def __init__(self, msg: bytes):
        self.msg = msg
        self.offset = 0
        self.parse()

    @staticmethod
    def __read_header(msg):
        header_byte = msg[0]
        message_type = (header_byte & 0xF0) >> 4
        message_flags = header_byte & 0x0F
        return message_type, message_flags, header_byte

    def read(self, length) -> bytes:
        value = self.msg[self.offset:self.offset + length]
        self.offset += length
        return value

    def read_byte(self) -> int:
        return self.read(1)[0]

    def read_short(self) -> int:
        return struct.unpack('>H', self.read(2))[0]

    def read_string(self) -> str:
        str_len = self.read_short()
        str_buf = self.read(str_len)
        return str_buf.decode('utf-8')

    def read_rest(self) -> bytes:
        return self.read(len(self.msg) - self.offset)

    def parse(self):
        self.message_type, self.message_flags, self.header_byte = MQTTMessage.__read_header(self.msg)
        self.offset += 2

    @abc.abstractmethod
    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        raise NotImplementedError()

class ConnectMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.protocol_name = self.read_string()
        self.protocol_version = self.read_byte()
        self.connect_flags = self.read_byte()
        self.keep_alive = self.read_short()
        self.client_id = self.read_string()

        self.needs_authentication = self.connect_flags & 0xC0
        self.__is_authenticated = not self.needs_authentication

        self.__username = None
        self.__password = None

        if self.needs_authentication:
            self.__read_authentication()

    def __read_authentication(self):
        if self.connect_flags & 0x80:
            self.__username = self.read_string()

            if not self.__username:
                raise ValueError('Username flag is set but no username provided')

        if self.connect_flags & 0x40:
            self.__password = self.read_string()

            if not self.__password:
                raise ValueError('Password flag is set but no password provided')

    def authenticate(self, authenticator: Authenticator):
        if not self.needs_authentication or self.__is_authenticated:
            return True

        self.__is_authenticated = authenticator.authenticate(self.__username, self.__password)
        return self.__is_authenticated

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_connect(client, self)

class PublishMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.topic_name = self.read_string()
        self.qos_level = (self.header_byte & 0x06) >> 1

        if self.qos_level > 0:
            self.packet_id = self.read_short()

        self.payload = self.read_rest()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_publish(client, self)

class ConnAckMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.ack_flags = self.read_byte()
        self.return_code = self.read_byte()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_connack(client, self)

class PubAckMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_puback(client, self)

class PubRecMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_pubrec(client, self)

class PubRelMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_pubrel(client, self)

class PubCompMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_pubcomp(client, self)

class SubscribeMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()

        print(f'Subscribe message packet ID: {self.packet_id}, {self.message_type}, {self.message_flags}, {self.offset} < {len(self.msg)}')
        self.topics = []

        while self.offset < len(self.msg):
            _ = self.read_byte()
            topic = self.read_string()
            qos = self.read_byte()
            print(f'Subscribe message topic: {topic}, qos: {qos}')
            self.topics.append((topic, qos))

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_subscribe(client, self)

class SubAckMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()
        self.return_codes = []

        while self.offset < len(self.msg):
            self.return_codes.append(self.read_byte())

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_suback(client, self)

class UnsubscribeMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()
        self.topics = []

        while self.offset < len(self.msg):
            topic = self.read_string()
            self.topics.append(topic)

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_unsubscribe(client, self)

class UnsubAckMessage(MQTTMessage):
    def parse(self):
        super().parse()
        self.packet_id = self.read_short()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_unsuback(client, self)

class PingReqMessage(MQTTMessage):
    def parse(self):
        super().parse()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_pingreq(client, self)

class PingRespMessage(MQTTMessage):
    def parse(self):
        super().parse()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_pingresp(client, self)

class DisconnectMessage(MQTTMessage):
    def parse(self):
        super().parse()

    def handle_message(self, handler: ProtocolHandlerInterface, client: Client):
        handler.handle_disconnect(client, self)
