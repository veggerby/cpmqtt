import struct
from MQTTLogger import Logger

class ProtocolHandler:
    SUPPORTED_PROTOCOLS = ['MQTT']

    def __init__(self, logger = None):
        self.logger = logger or Logger()

    def handle_connect(self, client, msg, broker):
        try:
            protocol_name_len = struct.unpack('>H', msg[2:4])[0]
            protocol_name = msg[4:4 + protocol_name_len].decode('utf-8')
            self.logger.debug(f'Protocol Name: {protocol_name}')

            if protocol_name not in ProtocolHandler.SUPPORTED_PROTOCOLS:
                raise ValueError('Unsupported protocol')

            protocol_version = msg[4 + protocol_name_len]
            connect_flags = msg[7 + protocol_name_len]
            keep_alive = struct.unpack('>H', msg[8 + protocol_name_len:10 + protocol_name_len])[0]
            client_id_len = struct.unpack('>H', msg[10 + protocol_name_len:12 + protocol_name_len])[0]
            client_id = msg[12 + protocol_name_len:12 + protocol_name_len + client_id_len].decode('utf-8')

            if not client_id:
                raise ValueError('Client ID must not be empty')

            broker.client_manager.add_client(client)
            ProtocolHandler.handle_authentication(client, connect_flags, msg, protocol_name_len, client_id_len, broker)

            connack_flags = 0
            return_code = 0  # Connection Accepted
            connack = struct.pack('>BB', 32, 2) + struct.pack('BB', connack_flags, return_code)
            client.send(connack)
            self.logger.debug(f'Client connected: {client_id}')

        except ValueError as ve:
            self.logger.error(f'Error in handle_connect: {ve}')
            client.send(struct.pack('>BB', 32, 2) + struct.pack('BB', 0, 1))  # Connection Refused, unacceptable protocol version
            client.close()
        except Exception as e:
            self.logger.error(f'Error in handle_connect: {e}')
            client.send(struct.pack('>BB', 32, 2) + struct.pack('BB', 0, 2))  # Connection Refused, identifier rejected
            client.close()

    def handle_authentication(self, client, connect_flags, msg, protocol_name_len, client_id_len, broker):
        index = 12 + protocol_name_len + client_id_len
        username = None
        password = None

        if connect_flags & 0x80:
            username_len = struct.unpack('>H', msg[index:index + 2])[0]
            index += 2
            username = msg[index:index + username_len].decode('utf-8')
            index += username_len

        if connect_flags & 0x40:
            password_len = struct.unpack('>H', msg[index:index + 2])[0]
            index += 2
            password = msg[index:index + password_len].decode('utf-8')

        if username and password:
            if not broker.authenticator.authenticate(username, password):
                raise ValueError('Authentication failed')
        elif connect_flags & 0xC0:
            raise ValueError('Username or Password flag is set but no credentials provided')

    def handle_publish(self, client, msg, broker):
        try:
            fixed_header_len = 1 + 1  # Control Packet Type + Remaining Length
            remaining_length = msg[1]
            topic_len = struct.unpack('>H', msg[fixed_header_len:fixed_header_len + 2])[0]
            topic_start = fixed_header_len + 2
            topic_end = topic_start + topic_len
            topic = msg[topic_start:topic_end].decode('utf-8')

            payload_start = topic_end
            payload = msg[payload_start:payload_start + remaining_length - 2 - topic_len]

            if not topic:
                raise ValueError('Topic must not be empty')

            self.logger.receive(f'Received message: {payload} on topic: {topic}')
            broker.topic_manager.publish(topic, msg)
            self.logger.send(f'{payload} published to topic: {topic}')

            qos_level = (msg[0] & 0x06) >> 1
            if qos_level == 1:  # QoS 1
                packet_id = struct.unpack('>H', msg[topic_end:topic_end + 2])[0]
                puback = struct.pack('>BBH', 64, 2, packet_id)
                client.send(puback)
            elif qos_level == 2:  # QoS 2
                raise NotImplementedError('QoS 2 not supported')

        except Exception as e:
            self.logger.error(f'Error in handle_publish: {e}')

    def handle_subscribe(self, client, msg, broker):
        try:
            packet_id = struct.unpack('>H', msg[2:4])[0]
            index = 4
            topics = []

            while index < len(msg):
                topic_len = struct.unpack('>H', msg[index:index + 2])[0]
                index += 2
                topic = msg[index:index + topic_len].decode('utf-8')
                index += topic_len
                qos = msg[index]
                index += 1

                if not topic:
                    raise ValueError('Topic must not be empty')

                broker.topic_manager.subscribe(topic, client)
                topics.append((topic, qos))

            self.logger.info(f"Client subscribed to topics: {topics}")
            suback = struct.pack('>BBH', 0x90, 2 + len(topics), packet_id) + bytes([qos for topic, qos in topics])
            client.send(suback)

        except Exception as e:
            self.logger.error(f'Error in handle_subscribe: {e}')

    def handle_unsubscribe(self, client, msg, broker):
        try:
            packet_id = struct.unpack('>H', msg[2:4])[0]
            index = 4
            topics = []

            while index < len(msg):
                topic_len = struct.unpack('>H', msg[index:index + 2])[0]
                index += 2
                topic = msg[index:index + topic_len].decode('utf-8')
                index += topic_len

                if not topic:
                    raise ValueError('Topic must not be empty')

                broker.topic_manager.unsubscribe(topic, client)
                topics.append(topic)

            self.logger.info(f"Client unsubscribed from topics: {topics}")
            unsuback = struct.pack('>BBH', 0xB0, 2, packet_id)
            client.send(unsuback)

        except Exception as e:
            self.logger.error(f'Error in handle_unsubscribe: {e}')

    def send_pingresp(self, client, broker):
        try:
            client.send(b'\xD0\x00')
            self.logger.send('PINGRESP sent to client')
        except Exception as e:
            self.logger.error(f'Error sending PINGRESP: {e}')

    def handle_disconnect(self, client, broker):
        try:
            self.logger.info('Client disconnected')
            broker.client_manager.remove_client(client)
            client.close()
        except Exception as e:
            self.logger.error(f'Error handling disconnect: {e}')
