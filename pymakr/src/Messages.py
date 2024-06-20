import struct

from Authenticator import Authenticator
from Client import Client
from ProtocolHandler import ProtocolHandler

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

ENCODING_UTF8 = 'utf-8'

class MQTTMessage:
    msg: bytes

    @staticmethod
    def create(msg) -> 'MQTTMessage':
        packet_type, _, _ = MQTTMessage.__read_fixed_header(msg)
        if packet_type == PACKET_TYPE_CONNECT:
            return ConnectMessage(msg)
        elif packet_type == PACKET_TYPE_CONNACK:
            raise ValueError("ConnAck message is a response and should not be created directly")
        elif packet_type == PACKET_TYPE_PUBLISH:
            return PublishMessage(msg)
        elif packet_type == PACKET_TYPE_PUBACK:
            return PubAckMessage(msg)
        elif packet_type == PACKET_TYPE_PUBREC:
            raise NotImplementedError('PubRec message not implemented')
        elif packet_type == PACKET_TYPE_PUBREL:
            raise NotImplementedError('PubRel message not implemented')
        elif packet_type == PACKET_TYPE_PUBCOMP:
            raise NotImplementedError('PubComp message not implemented')
        elif packet_type == PACKET_TYPE_SUBSCRIBE:
            return SubscribeMessage(msg)
        elif packet_type == PACKET_TYPE_SUBACK:
            raise ValueError("SubAck message is a response and should not be created directly")
        elif packet_type == PACKET_TYPE_UNSUBSCRIBE:
            return UnsubscribeMessage(msg)
        elif packet_type == PACKET_TYPE_UNSUBACK:
            raise ValueError("UnSubAck message is a response and should not be created directly")
        elif packet_type == PACKET_TYPE_PINGREQ:
            return PingReqMessage(msg)
        elif packet_type == PACKET_TYPE_PINGRESP:
            raise ValueError("PingResp message is a response and should not be created directly")
        elif packet_type == PACKET_TYPE_DISCONNECT:
            return DisconnectMessage(msg)
        else:
            raise ValueError(f'Unsupported message type: {packet_type}')

    def __init__(self, packet_type: int, msg: bytes = None):
        self.packet_type = packet_type
        self.flags = 0
        self.msg = msg or b''
        self.offset = 0

        if msg:
            self.__read_packet()

    @staticmethod
    def __read_fixed_header(msg):
        control_field = msg[0]
        packet_type = (control_field & 0xF0) >> 4
        flags = control_field & 0x0F
        return packet_type, flags, control_field

    def read(self, length, move = True) -> bytes:
        if (self.offset + length > len(self.msg)):
            raise ValueError(f'Message length exceeded: {self.offset}:{self.offset + length} >= {len(self.msg)}')

        buf = self.msg[self.offset:self.offset + length]

        if move:
            self.offset += length

        return buf

    def write(self, buf: bytes):
        self.msg += buf

    def read_byte(self) -> int:
        if (self.offset >= len(self.msg)):
            raise ValueError(f'Message length exceeded: {self.offset} >= {len(self.msg)}')

        byte = self.msg[self.offset]
        self.offset += 1
        return byte

    def write_byte(self, byte: int):
        self.msg += struct.pack('>B', byte & 0xFF)

    def read_short(self) -> int:
        return struct.unpack('>H', self.read(2))[0]

    def write_short(self, short: int):
        self.msg += struct.pack('>H', short)

    def read_string(self, encoding: str = ENCODING_UTF8) -> str:
        str_len = self.read_short()
        str_buf = self.read(str_len)
        return str_buf.decode(encoding)

    def write_string(self, str: str, encoding: str = ENCODING_UTF8):
        str_buf = str.encode(encoding)
        self.write_short(len(str_buf))
        self.msg += str_buf

    def __read_rest(self) -> bytes:
        return self.read(len(self.msg) - self.offset, False)

    def __read_remaining_length(self) -> int:
        length = 0
        multiplier = 1
        while True:
            encoded_byte = self.read_byte()
            length += (encoded_byte & 127) * multiplier
            if (encoded_byte & 128) == 0:
                break
            multiplier *= 128

        return length

    def __read_packet(self):
        self.packet_type, self.flags, self.control_field = MQTTMessage.__read_fixed_header(self.msg)

        self.dup = (self.flags & 0x08) == 0x08
        self.qos = (self.flags & 0x06) >> 1
        self.retain = (self.flags & 0x01) == 0x01

        self.offset = 1
        self.remaining_length = self.__read_remaining_length()

        variable_header_start = self.offset
        self.read_variable_header()
        self.variable_header = self.msg[variable_header_start:self.offset]
        self.variable_header_length = len(self.variable_header)
        self.payload_length = self.remaining_length - self.variable_header_length

        # print(f'Packet type: {self.packet_type}, flags: {self.flags}, control field: {self.control_field}, remaining length: {self.remaining_length}, variable header length: {self.variable_header_length}, payload length: {self.payload_length}')

        self.payload = self.__read_rest()
        self.read_payload()

    def read_variable_header(self):
        pass

    def read_payload(self):
        pass

    def write_message(self):
        pass

    def __get_remaining_length(self, remaining_length: int) -> bytes:
        remaining_length_buf = b''
        length = remaining_length
        while True:
            encoded_byte = length % 128
            length //= 128
            if length > 0:
                encoded_byte |= 128

            remaining_length_buf += struct.pack('>B', encoded_byte)

            if length == 0:
                break

        return remaining_length_buf

    def write(self):
        self.offset = 0
        self.msg = b''
        self.write_message()
        remaining_length = len(self.msg)
        self.msg = struct.pack('>B', (self.packet_type << 4) | (self.flags & 0x0F)) + self.__get_remaining_length(remaining_length) + self.msg

    def handle_message(self, handler: ProtocolHandler, client: Client):
        pass

    def send_to(self, client: Client, send_as_is = False):
        if not send_as_is:
            self.write()

        print(f'Sending message: {self.msg!r}')
        client.send(self.msg)

class ConnectMessage(MQTTMessage):
    def __init__(self, msg: bytes = None):
        super().__init__(PACKET_TYPE_CONNECT, msg)

    def read_variable_header(self):
        self.protocol_name = self.read_string()
        self.protocol_version = self.read_byte()
        self.connect_flags = self.read_byte()
        self.keep_alive = self.read_short()

        self.flag_username = (self.connect_flags & 0x80) == 0x80
        self.flag_password = (self.connect_flags & 0x40) == 0x40
        self.flag_will_retain = (self.connect_flags & 0x20) == 0x20
        self.flag_will_qos = (self.connect_flags & 0x18) >> 3
        self.flag_will_flag = (self.connect_flags & 0x04) == 0x04
        self.flag_clean_session = (self.connect_flags & 0x02) == 0x02

        self.needs_authentication = self.flag_username or self.flag_password
        self.__is_authenticated = not self.needs_authentication

    def read_payload(self):
        self.client_id = self.read_string()

        self.__username = None
        self.__password = None

        if self.needs_authentication:
            self.__read_authentication()

    def __read_authentication(self):
        if self.flag_username:
            self.__username = self.read_string()

            if not self.__username:
                raise ValueError('Username flag is set but no username provided')

        if self.flag_password:
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

class ConnAckMessage(MQTTMessage):
    conn_ack_flags: int = 0
    return_code: int = 0

    def __init__(self, conn_ack_flags: int = 0, return_code: int = 0):
        super().__init__(PACKET_TYPE_CONNACK)
        self.conn_ack_flags = conn_ack_flags
        self.return_code = return_code

    def write_message(self):
        self.write_byte(self.conn_ack_flags)
        self.write_byte(self.return_code)

class PublishMessage(MQTTMessage):
    def __init__(self, msg: bytes = None):
        super().__init__(PACKET_TYPE_PUBLISH, msg)

    def read_variable_header(self):
        self.topic_name = self.read_string()
        if self.qos > 0:
            self.packet_id = self.read_short()
        else:
            self.packet_id = None

    def handle_message(self, handler: ProtocolHandler, client: Client):
        handler.handle_publish(client, self)

class PubAckMessage(MQTTMessage):
    def __init__(self, publish_message: PublishMessage = None, msg: bytes = None):
        super().__init__(PACKET_TYPE_PUBACK, msg)
        self.publish_message = publish_message

    def read_variable_header(self):
        self.packet_id = self.read_short()

    def write_message(self):
        self.write_short(self.publish_message.packet_id)

class SubscribeMessage(MQTTMessage):
    packet_id: int = 0
    topic: str = ''
    qos: int = 0

    def __init__(self, msg: bytes):
        super().__init__(PACKET_TYPE_SUBSCRIBE, msg)

    def read_variable_header(self):
        self.packet_id = self.read_short()

    def read_payload(self):
        self.topic = self.read_string()
        self.qos = self.read_byte()

    def handle_message(self, handler: ProtocolHandler, client: Client):
        handler.handle_subscribe(client, self)

class SubAckMessage(MQTTMessage):
    def __init__(self, subscribe_message: SubscribeMessage):
        super().__init__(PACKET_TYPE_SUBACK)
        self.subscribe_message = subscribe_message

    def write_message(self):
        self.write_byte(self.subscribe_message.packet_id)
        self.write_byte(self.subscribe_message.qos)

class UnsubscribeMessage(MQTTMessage):
    packet_id: int = 0
    topic: str = ''

    def __init__(self, msg: bytes):
        super().__init__(PACKET_TYPE_UNSUBSCRIBE, msg)

    def read_variable_header(self):
        self.packet_id = self.read_short()

    def read_payload(self):
        self.topic = self.read_string()

    def handle_message(self, handler: ProtocolHandler, client: Client):
        handler.handle_unsubscribe(client, self)

class UnSubAckMessage(MQTTMessage):
    def __init__(self, unsubscribe_message: UnsubscribeMessage):
        super().__init__(PACKET_TYPE_UNSUBACK)
        self.unsubscribe_message = unsubscribe_message

    def write_message(self):
        self.write_byte(self.unsubscribe_message.packet_id)

class PingReqMessage(MQTTMessage):
    def __init__(self, msg: bytes):
        super().__init__(PACKET_TYPE_PINGREQ, msg)

    def handle_message(self, handler: ProtocolHandler, client: Client):
        handler.handle_pingreq(client, self)

class PingRespMessage(MQTTMessage):
    def __init__(self, pingreq_message: PingReqMessage):
        super().__init__(PACKET_TYPE_PINGRESP)
        self.pingreq_message = pingreq_message

class DisconnectMessage(MQTTMessage):
    def __init__(self, msg: bytes):
        super().__init__(PACKET_TYPE_DISCONNECT, msg)

    def handle_message(self, handler: ProtocolHandler, client: Client):
        handler.handle_disconnect(client, self)
