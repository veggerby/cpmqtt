import usocket as socket
import ustruct as struct
import network
import time
import gc
import threading
import random
import machine, neopixel
from machine import Timer

class MQTTLogger:
    HEADER = '\033[95m'
    SEND = '\033[94m'
    RECEIVE = '\033[96m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CLEAR = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def debug(message, debug):
        if debug:
            print(f'{MQTTLogger.HEADER}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def info(message, debug):
        if debug:
            print(f'{MQTTLogger.INFO}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def warning(message, debug):
        if debug:
            print(f'{MQTTLogger.WARNING}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def error(message, debug):
        if debug:
            print(f'{MQTTLogger.ERROR}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def send(message, debug):
        if debug:
            print(f'{MQTTLogger.SEND}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def receive(message, debug):
        if debug:
            print(f'{MQTTLogger.RECEIVE}{message}{MQTTLogger.CLEAR}')


class ClientManager:
    def __init__(self):
        self.clients = {}

    def add_client(self, client_socket):
        self.clients[client_socket] = {}

    def remove_client(self, client_socket):
        del self.clients[client_socket]

    def get_client_by_id(self, client_id):
        return self.clients.get(client_id)

    def cleanup_clients(self):
        for client in list(self.clients.keys()):
            if not self.is_socket_open(client):
                MQTTLogger.warning(f'Removing closed client: {client}', debug=True)
                self.remove_client(client)
                client.close()

    @staticmethod
    def is_socket_open(sock):
        try:
            sock.send(b'')
            return True
        except OSError:
            return False


class ProtocolHandler:
    SUPPORTED_PROTOCOLS = ['MQTT']

    @staticmethod
    def handle_connect(client, msg, broker):
        try:
            protocol_name_len = struct.unpack('>H', msg[2:4])[0]
            protocol_name = msg[4:4 + protocol_name_len].decode('utf-8')
            MQTTLogger.debug(f'Protocol Name: {protocol_name}', broker.debug)

            if protocol_name not in ProtocolHandler.SUPPORTED_PROTOCOLS:
                raise ValueError('Unsupported protocol')

            protocol_version = msg[4 + protocol_name_len]
            connect_flags = msg[7 + protocol_name_len]
            client_id_len = struct.unpack('>H', msg[10 + protocol_name_len + 1:12 + protocol_name_len + 1])[0]
            client_id = msg[12 + protocol_name_len + 1:12 + protocol_name_len + 1 + client_id_len].decode('utf-8')

            broker.client_manager.add_client(client_id)
            ProtocolHandler.handle_authentication(client, connect_flags, msg, protocol_name_len, client_id_len, broker)

            client.send(b'\x20\x02\x00\x00')  # CONNACK with 0x00 connection accepted
            MQTTLogger.debug(f'Client connected: {client_id}', broker.debug)

        except ValueError as ve:
            MQTTLogger.error(f'Error in handle_connect: {ve}', broker.debug)
            client.close()
        except Exception as e:
            MQTTLogger.error(f'Error in handle_connect: {e}', broker.debug)
            client.close()

    @staticmethod
    def handle_authentication(client, connect_flags, msg, protocol_name_len, client_id_len, broker):
        if connect_flags & 0x80:
            user_name_flag = connect_flags & 0x80
            password_flag = connect_flags & 0x40
            index = 12 + protocol_name_len + 1 + client_id_len
            if user_name_flag:
                user_name_len = struct.unpack('>H', msg[index:index + 2])[0]
                index += 2
                user_name = msg[index:index + user_name_len].decode('utf-8')
                index += user_name_len
            if password_flag:
                password_len = struct.unpack('>H', msg[index:index + 2])[0]
                index += 2
                password = msg[index:index + password_len].decode('utf-8')

            if not broker.authenticate(user_name, password):
                MQTTLogger.error(f'Authentication failed for user: {user_name}', broker.debug)
                client.send(b'\x20\x02\x00\x04')  # CONNACK with 0x04 connection refused: bad username or password
                client.close()
                raise ValueError('Authentication failed')

    @staticmethod
    def handle_publish(client, msg, broker):
        try:
            topic_len = struct.unpack('>H', msg[2:4])[0]
            topic = msg[4:4 + topic_len].decode('utf-8')
            payload = msg[4 + topic_len:]
            MQTTLogger.receive(f'Received message: {payload} on topic: {topic}', broker.debug)

            if topic in broker.topics:
                for subscriber in broker.topics[topic]:
                    try:
                        subscriber.send(msg)
                    except OSError as e:
                        MQTTLogger.error(f'Error forwarding message to subscriber: {e}', broker.debug)
                        broker.topics[topic].remove(subscriber)
            else:
                MQTTLogger.warning(f'No subscribers for topic: {topic}', broker.debug)

            MQTTLogger.send(f'{payload} published to topic: {topic}', broker.debug)
        except Exception as e:
            MQTTLogger.error(f'Error in handle_publish: {e}', broker.debug)

    @staticmethod
    def handle_subscribe(client, msg, broker):
        try:
            MQTTLogger.debug(f"Received subscription message: {msg}", broker.debug)
            topics = []
            packet_id = msg[2:4]
            index = 4
            if msg[5] == 0:
                index += 1

            while index < len(msg):
                topic_len = struct.unpack('>H', msg[index:index + 2])[0]
                index += 2
                topic = msg[index:index + topic_len].decode('utf-8')
                index += topic_len
                qos = msg[index] if index < len(msg) else 0
                index += 1

                if topic not in broker.topics:
                    broker.topics[topic] = []
                broker.topics[topic].append(client)
                topics.append((topic, qos))

            MQTTLogger.info(f"Client subscribed to topics: {topics}", broker.debug)
            response = b'\x90' + struct.pack('>H', len(packet_id)) + packet_id
            for topic, qos in topics:
                response += struct.pack('B', qos)

            client.send(response)
        except Exception as e:
            MQTTLogger.error(f'Error in handle_subscribe: {e}', broker.debug)

    @staticmethod
    def handle_unsubscribe(client, msg, broker):
        try:
            MQTTLogger.debug(f"Received unsubscribe message: {msg}", broker.debug)
            topics = []
            packet_id = msg[2:4]
            index = 4
            if msg[5] == 0:
                index += 1

            while index < len(msg):
                topic_len = struct.unpack('>H', msg[index:index + 2])[0]
                index += 2
                topic = msg[index:index + topic_len].decode('utf-8')
                index += topic_len

                if topic in broker.topics:
                    broker.topics[topic].remove(client)
                    if not broker.topics[topic]:
                        del broker.topics[topic]
                    topics.append(topic)

            MQTTLogger.info(f"Client unsubscribed from topics: {topics}", broker.debug)
            response = b'\xB0' + struct.pack('>H', len(packet_id)) + packet_id
            client.send(response)
        except Exception as e:
            MQTTLogger.error(f'Error in handle_unsubscribe: {e}', broker.debug)

    @staticmethod
    def send_pingresp(client, broker):
        try:
            client.send(b'\xD0\x00')
            MQTTLogger.send('PINGRESP sent to client', broker.debug)
        except Exception as e:
            MQTTLogger.error(f'Error sending PINGRESP: {e}', broker.debug)

    @staticmethod
    def handle_disconnect(client, broker):
        try:
            MQTTLogger.info('Client disconnected', broker.debug)
            broker.client_manager.remove_client(client)
            client.close()
        except Exception as e:
            MQTTLogger.error(f'Error handling disconnect: {e}', broker.debug)


class MQTTBroker:
    DEFAULT_TIMEOUT = 20.0
    ACCEPT_TIMEOUT = 60.0
    DEFAULT_PORT = 1883

    def __init__(self, host='0.0.0.0', port=DEFAULT_PORT, rgb_led=4, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.rgb_led = rgb_led
        self.topics = {}
        self.client_manager = ClientManager()
        self.led = neopixel.NeoPixel(machine.Pin(rgb_led), 1) if rgb_led > 0 else None
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        MQTTLogger.info(f'Starting MQTT Broker on {self.host}:{self.port}', self.debug)

        while True:
            self.sock.settimeout(self.ACCEPT_TIMEOUT)
            try:
                client, address = self.sock.accept()
                client.settimeout(self.DEFAULT_TIMEOUT)
                MQTTLogger.info(f'New connection from {address}', self.debug)
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except socket.timeout:
                pass
            self.client_manager.cleanup_clients()
            gc.collect()

    def handle_client(self, client):
        while True:
            try:
                msg = client.recv(2048)
                if not msg:
                    break
                MQTTLogger.receive(f"Received message: {msg}", self.debug)
                msg_type = msg[0] >> 4

                if msg_type == 1:
                    ProtocolHandler.handle_connect(client, msg, self)
                elif msg_type == 3:
                    ProtocolHandler.handle_publish(client, msg, self)
                elif msg_type == 8:
                    ProtocolHandler.handle_subscribe(client, msg, self)
                elif msg_type == 10:
                    ProtocolHandler.handle_unsubscribe(client, msg, self)
                elif msg_type == 12:
                    ProtocolHandler.send_pingresp(client, self)
                elif msg_type == 14:
                    ProtocolHandler.handle_disconnect(client, self)
                    break
                else:
                    MQTTLogger.error(f"Unknown message type: {msg_type}", self.debug)
            except Exception as e:
                MQTTLogger.error(f'Error in handle_client: {e}', self.debug)
                break

        client.close()

    def authenticate(self, username, password):
        # Replace with actual authentication logic
        return username == "admin" and password == "password"

    def set_led(self, color):
        if self.rgb_led > 0:
            self.led[0] = color
            self.led.write()

if __name__ == "__main__":
    broker = MQTTBroker(host='0.0.0.0', port=1883, rgb_led=4, debug=True)
    broker.start()
