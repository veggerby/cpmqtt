import struct
import abc

from MQTTAuthenticator import Authenticator
from MQTTClient import Client
from MQTTProtocolHandler import ProtocolHandler

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
    @staticmethod
    def create(msg) -> 'MQTTMessage':
        message_type, _, _ = MQTTMessage.__read_header(msg)
        if message_type == MESSAGE_TYPE_CONNECT:
            return ConnectMessage(msg)
        elif message_type == MESSAGE_TYPE_CONNACK:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_PUBLISH:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_PUBACK:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_PUBREC:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_PUBREL:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_PUBCOMP:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_SUBSCRIBE:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_SUBACK:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_UNSUBSCRIBE:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_UNSUBACK:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_PINGREQ:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_PINGRESP:
            raise NotImplementedError()
        elif message_type == MESSAGE_TYPE_DISCONNECT:
            raise NotImplementedError()
        else:
            raise ValueError(f'Unsupported message type: {message_type}')

    def __init__(self, msg):
        self.msg = msg
        self.parse()

    @staticmethod
    def __read_header(msg):
        header_byte = msg[0]
        message_type = (header_byte & 0xF0) >> 4
        message_flags = header_byte & 0x0F
        return message_type, message_flags, header_byte

    def reset(self):
        self.set_offset(0)

    def set_offset(self, offset):
        self.offset = offset

    def skip(self, length) -> int:
        self.offset += length
        return self.offset

    def read(self, length) -> bytes:
        value = self.msg[self.offset:self.offset + length]
        self.offset += length
        return value

    def read_byte(self) -> int:
        value = self.read(1)[0]
        return value

    def read_short(self) -> int:
        value = struct.unpack('>H', self.read(2))[0]
        return value

    def read_string(self) -> str:
        str_len = self.read_short()
        value = self.read(str_len).decode('utf-8')
        return value

    def read_remaining_length(self) -> int:
        length = 0
        multiplier = 1
        while True:
            encoded_byte = self.read_byte()
            length += (encoded_byte & 127) * multiplier
            if (encoded_byte & 128) == 0:
                break
            multiplier *= 128
        return length

    def parse(self):
        self.message_type, self.message_flags, self.header_byte = MQTTMessage.__read_header(self.msg)

    @abc.abstractmethod
    def handle_message(self, handler: ProtocolHandler, client: Client):
        raise NotImplementedError()

class ConnectMessage(MQTTMessage):
    def __init__(self, msg):
        super().__init__(MESSAGE_TYPE_CONNECT, msg)

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

    def handle_message(self, handler: ProtocolHandler, client: Client):
        handler.handle_connect(client, self)


class PublishMessage(MQTTMessage):
    def __init__(self, msg):
        super().__init__(MESSAGE_TYPE_PUBLISH, msg)

    def parse(self):
        super().parse()

        self.remaining_length = self.read_remaining_length()
        self.topic_name = self.read_string()
        self.payload = self.read(self.remaining_length)
        self.qos_level = (self.header_byte & 0x06) >> 1

        if (self.qos_level == 1):
            self.packet_id = self.read_short()

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

    def handle_message(self, handler: ProtocolHandler, client: Client):
        handler.handle_connect(client, self)
