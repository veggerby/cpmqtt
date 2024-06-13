import usocket as socket
import ustruct as struct
import network
import time
import gc
import threading
import random
import machine, neopixel
from machine import Timer

class MQTTBroker:
    HEADER = '\033[95m'
    SEND = '\033[94m'
    RECEIVE = '\033[96m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CLEAR = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    DEFAULT_TIMEOUT = 20.0
    ACCEPT_TIMEOUT = 60.0
    DEFAULT_PORT = 1883
    SUPPORTED_PROTOCOLS = ['MQTT']

    def __init__(self, host='0.0.0.0', port=DEFAULT_PORT, rgb_led=-1, debug=False):
        self.host = host
        self.port = port
        self.clients = {}
        self.topics = {}
        self.rgb_led = rgb_led
        self.debug = debug
        self.tim0 = Timer(0)
        if rgb_led > 0:
            self.led = neopixel.NeoPixel(machine.Pin(rgb_led), 1)
            self.set_led((0, 255, 0))

    def add_client(self, client_socket):
        self.clients[client_socket] = {}

    def remove_client(self, client_socket):
        del self.clients[client_socket]

    def start(self):
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        s = socket.socket()
        s.bind(addr)
        s.listen(5)
        self.printI(f"MQTT broker listening on {self.host}:{self.port}")

        while True:
            try:
                cl, addr = s.accept()
                self.printI(f'Client connected from {addr}')
                cl.settimeout(self.ACCEPT_TIMEOUT)
                self.add_client(cl)
                threading.Thread(target=self.handle_client, args=(cl,)).start()
            except Exception as e:
                self.printE(f'Error: {e}')
                self.cleanup_clients()

    def handle_client(self, client):
        client.settimeout(self.DEFAULT_TIMEOUT)
        buffer = b''
        try:
            while True:
                msg = client.recv(2048)
                if not msg:
                    self.printE("No message received, closing connection.")
                    self.remove_client(client)
                    break

                buffer += msg
                while len(buffer) >= 2:
                    remaining_length, multiplier = 0, 1
                    for i in range(1, len(buffer)):
                        byte = buffer[i]
                        remaining_length += (byte & 0x7f) * multiplier
                        if (byte & 0x80) == 0:
                            break
                        multiplier *= 128

                    total_length = 1 + i + remaining_length
                    if len(buffer) < total_length:
                        break

                    msg = buffer[:total_length]
                    buffer = buffer[total_length:]

                self.printD(f'Received message: {msg} - {((msg[0] & 0xF0) >> 4)}')
                msg_type = (msg[0] & 0xF0) >> 4
                self.printD(f'Message type: {msg_type}')
                if msg_type == 1:  # CONNECT
                    self.handle_connect(client, msg)
                elif msg_type == 3:  # PUBLISH
                    self.handle_publish(client, msg)
                    self.set_led((0, 0, 255))
                elif msg_type == 8:  # SUBSCRIBE
                    self.handle_subscribe(client, msg)
                    self.set_led((42, 255, 246))
                elif msg_type == 10:  # UNSUBSCRIBE
                    self.handle_unsubscribe(client, msg)
                    self.set_led((235, 255, 0))
                elif msg_type == 12:  # PINGREQ
                    self.send_pingresp(client)
                elif msg_type == 14:  # DISCONNECT
                    self.handle_disconnect(client)
                else:
                    self.printW(f'Unknown message type: {msg_type}')

                self.tim0.init(period=750, mode=Timer.ONE_SHOT, callback=self.reset_led)
        except Exception as e:
            self.printE(f'Client handling error: {e}')
            self.remove_client(client)
            self.set_led((255, 0, 0))
        finally:
            self.printW('Closing client connection.')
            client.close()

    def reset_led(self, tim):
        self.set_led((0, 255, 0))

    def handle_connect(self, client, msg):
        if len(msg) > 3:
            try:
                protocol_name_len = struct.unpack('>H', msg[2:4])[0]
                protocol_name = msg[4:4 + protocol_name_len].decode('utf-8')
                self.printD(f'Protocol Name: {protocol_name}')

                if protocol_name not in self.SUPPORTED_PROTOCOLS:
                    self.printE(f'Unsupported protocol: {protocol_name}')
                    raise ValueError('Unsupported protocol')

                protocol_version = msg[4 + protocol_name_len]
                self.printD(f'Protocol Version: {protocol_version}')

                connect_flags = msg[7 + protocol_name_len]
                self.printD(f'Connect Flags: {connect_flags}')

                client_id_len = struct.unpack('>H', msg[10 + protocol_name_len + 1:12 + protocol_name_len + 1])[0]
                client_id = msg[12 + protocol_name_len + 1:12 + protocol_name_len + 1 + client_id_len].decode('utf-8')
                self.clients[client_id] = client
                self.handle_authentication(client, connect_flags, msg, protocol_name_len)

                client.send(b'\x20\x02\x00\x00')  # CONNACK with 0x00 connection accepted
                self.printD(f'Client connected: {client_id}')

            except ValueError as ve:
                self.printE(f'Error in handle_connect: {ve}')
                client.close()
            except Exception as e:
                self.printE(f'Error in handle_connect: {e}')
                client.close()
        else:
            client_id = random.randrange(0, 255)
            self.clients[client_id] = client
            client.send(b'\x20\x02\x00\x00')  # CONNACK with 0x00 connection accepted

    def handle_authentication(self, client, connect_flags, msg, protocol_name_len):
        if connect_flags & 0x80:
            user_name_flag = connect_flags & 0x80
            password_flag = connect_flags & 0x40
            index = 12 + protocol_name_len + 1 + client_id_len
            if user_name_flag:
                user_name_len = struct.unpack('>H', msg[index:index+2])[0]
                index += 2
                user_name = msg[index:index+user_name_len].decode('utf-8')
                index += user_name_len
            if password_flag:
                password_len = struct.unpack('>H', msg[index:index+2])[0]
                index += 2
                password = msg[index:index+password_len].decode('utf-8')

            if not self.authenticate(user_name, password):
                self.printE(f'Authentication failed for user: {user_name}')
                client.send(b'\x20\x02\x00\x04')  # CONNACK with 0x04 connection refused: bad username or password
                client.close()
                raise ValueError('Authentication failed')

    def authenticate(self, user_name, password):
        # Replace with actual authentication logic
        return user_name == "admin" and password == "password"

    def handle_publish(self, client, msg):
        try:
            topic_len = struct.unpack('>H', msg[2:4])[0]
            topic = msg[4:4 + topic_len].decode('utf-8')
            payload = msg[4 + topic_len:]
            self.printR(f'Received message: {payload} on topic: {topic}')

            if topic in self.topics:
                for subscriber in self.topics[topic]:
                    try:
                        subscriber.send(msg)
                    except OSError as e:
                        self.printE(f'Error forwarding message to subscriber: {e}')
                        self.topics[topic].remove(subscriber)
            else:
                self.printW(f'No subscribers for topic: {topic}')

            self.printS(f'{payload} published to topic: {topic}')
        except Exception as e:
            self.printE(f'Error in handle_publish: {e}')

    def handle_subscribe(self, client, msg):
        try:
            self.printD(f"Received subscription message: {msg}")
            topics = []
            packet_id = msg[2:4]
            index = 4
            if msg[5] == 0:
                index += 1

            while index < len(msg):
                if index + 2 > len(msg):
                    raise ValueError(f"Invalid message: unable to read topic length at index {index}")

                topic_len = struct.unpack('>H', msg[index:index+2])[0]
                index += 2
                self.printD(f"Read topic length: {topic_len} at index {index - 2}")

                if index + topic_len > len(msg):
                    raise ValueError(f"Invalid message: topic length exceeds message length ({topic_len} > {len(msg) - index})")

                topic = msg[index:index+topic_len].decode('utf-8')
                index += topic_len
                qos = msg[index] if index < len(msg) else 0
                index += 1
                self.printD(f"Read topic: {topic}, qos: {qos} at index {index - 1}")

                if topic not in self.topics:
                    self.topics[topic] = []
                self.topics[topic].append(client)
                topics.append((topic, qos))

            self.printI(f"Client subscribed to topics: {topics}")
            response = b'\x90' + struct.pack('>H', len(packet_id)) + packet_id
            for topic, qos in topics:
                response += struct.pack('B', qos)

            client.send(response)
        except Exception as e:
            self.printE(f'Error in handle_subscribe: {e}')

    def handle_unsubscribe(self, client, msg):
        try:
            self.printD(f"Received unsubscribe message: {msg}")
            topics = []
            packet_id = msg[2:4]
            index = 4
            if msg[5] == 0:
                index += 1

            while index < len(msg):
                topic_len = struct.unpack('>H', msg[index:index+2])[0]
                index += 2
                topic = msg[index:index+topic_len].decode('utf-8')
                index += topic_len

                if topic in self.topics:
                    self.topics[topic].remove(client)
                    if not self.topics[topic]:
                        del self.topics[topic]
                    topics.append(topic)

            self.printI(f"Client unsubscribed from topics: {topics}")
            response = b'\xB0' + struct.pack('>H', len(packet_id)) + packet_id
            client.send(response)
        except Exception as e:
            self.printE(f'Error in handle_unsubscribe: {e}')

    def send_pingresp(self, client):
        try:
            client.send(b'\xD0\x00')
            self.printS('PINGRESP sent to client')
        except Exception as e:
            self.printE(f'Error sending PINGRESP: {e}')

    def handle_disconnect(self, client):
        try:
            self.printI('Client disconnected')
            self.remove_client(client)
            client.close()
        except Exception as e:
            self.printE(f'Error handling disconnect: {e}')

    def is_socket_open(self, sock):
        try:
            sock.send(b'')
            return True
        except OSError:
            return False

    def cleanup_clients(self):
        for client in list(self.clients.keys()):
            if not self.is_socket_open(client):
                self.printW(f'Removing closed client: {client}')
                self.remove_client(client)
                client.close()

    def set_led(self, color):
        if self.rgb_led > 0:
            self.led[0] = color
            self.led.write()

    def printD(self, message):
        if self.debug:
            print(f'{self.HEADER}{message}{self.CLEAR}')

    def printI(self, message):
        if self.debug:
            print(f'{self.INFO}{message}{self.CLEAR}')

    def printW(self, message):
        if self.debug:
            print(f'{self.WARNING}{message}{self.CLEAR}')

    def printE(self, message):
        if self.debug:
            print(f'{self.ERROR}{message}{self.CLEAR}')

    def printS(self, message):
        if self.debug:
            print(f'{self.SEND}{message}{self.CLEAR}')

    def printR(self, message):
        if self.debug:
            print(f'{self.RECEIVE}{message}{self.CLEAR}')

if __name__ == "__main__":
    broker = MQTTBroker(host='0.0.0.0', port=1883, rgb_led=4, debug=True)
    broker.start()
