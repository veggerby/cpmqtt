import usocket as socket
import ustruct as struct
import ubinascii as binascii
import ujson as json
import network
import time
import gc
import threading
import random
import machine, neopixel
from machine import Timer

class MQTTBroker:
    def __init__(self, host='0.0.0.0', port=1883, rgb_led = -1, debug = False):
        self.host = host
        self.port = port
        self.clients = {}
        self.topics = {}
        self.rgb_led = rgb_led
        self.debug = debug
        self.tim0 = Timer(0)
        if rgb_led > 0:
            self.led = neopixel.NeoPixel(machine.Pin(rgb_led), 1)
            self.set_led((0,255,0))

    def add_client(self, client_socket):
        # Add a new client to the list of connected clients
        self.clients[client_socket] = {}

    def remove_client(self, client_socket):
        # Remove a client from the list of connected clients
        del self.clients[client_socket]

    def start(self):
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        s = socket.socket()
        s.bind(addr)
        s.listen(5)
        self.printI(f"Info: MQTT broker listening on {self.host}:{self.port}")

        while True:
            try:
                cl, addr = s.accept()
                self.printI(f'Info: Client connected from {addr}')
                cl.settimeout(60.0)
                self.add_client(cl)
                threading.Thread(target=self.handle_client, args=(cl,)).start()
            except Exception as e:
                self.printE(f'Error: {e}')
                self.cleanup_clients()

    def handle_client(self, client):
        client.settimeout(20.0)  # Increase timeout to 20 seconds
        buffer = b''
        try:
            while True:
                msg = client.recv(2048)
                if not msg:
                    self.printE("Error: No message received, closing connection.")
                    self.remove_client(client)
                    break
                
                buffer += msg
                while len(buffer) >= 2:
                    # Get the remaining length of the MQTT message
                    remaining_length, multiplier = 0, 1
                    for i in range(1, len(buffer)):
                        byte = buffer[i]
                        remaining_length += (byte & 0x7f) * multiplier
                        if (byte & 0x80) == 0:
                            break
                        multiplier *= 128

                    total_length = 1 + i + remaining_length
                    if len(buffer) < total_length:
                        # Wait for the complete message
                        break

                    msg = buffer[:total_length]
                    buffer = buffer[total_length:]
                
                self.printD(f'Debug: Received message:{msg} - {((msg[0] & 0xF0) >> 4)}' )
                msg_type = (msg[0] & 0xF0) >> 4
                self.printD(f'Debug: Message type: {msg_type}')
                if msg_type == 1:  # CONNECT
                    self.handle_connect(client, msg)
                elif msg_type == 3:  # PUBLISH
                    self.handle_publish(client, msg)
                    self.set_led(( 0, 0, 255))
                elif msg_type == 8:  # SUBSCRIBE
                    self.handle_subscribe(client, msg)
                    self.set_led(( 42, 255, 246))
                elif msg_type == 10:  # UNSUBSCRIBE
                    self.handle_unsubscribe(client, msg)
                    self.set_led(( 235, 255, 0))
                elif msg_type == 12:  # PINGREQ
                    self.send_pingresp(client)
                elif msg_type == 14:  # DISCONNECT
                    self.handle_disconnect(client)
                else:
                    self.printW(f'Warning: Unknown message type: {msg_type}')
                
                self.tim0.init(period=750, mode=Timer.ONE_SHOT, callback=self.reset_led)
        except Exception as e:
            self.printE(f'Error: Client handling error: {e}')
            self.remove_client(client)
            self.set_led(( 255, 0, 0))
        finally:
            self.printW('Warning: Closing client connection.')
            client.close()
            
    def reset_led(self, tim):
        self.set_led(( 0, 255, 0))

    def handle_connect(self, client, msg):
        if len(msg) > 3:
            try:
                protocol_name_len = struct.unpack('>H', msg[2:4])[0]
                protocol_name = msg[4:4 + protocol_name_len].decode('utf-8')
                self.printD(f'Debug: Protocol Name: {protocol_name}')
                
                # Check if the protocol name is MQTT
                if protocol_name != 'MQTT':
                    self.printE(f'Error: Unsupported protocol: {protocol_name}')
                    raise ValueError('Unsupported protocol')
                
                client_id_len = struct.unpack('>H', msg[10 + protocol_name_len + 1:12 + protocol_name_len + 1])[0]
                client_id = msg[12 + protocol_name_len + 1:12 + protocol_name_len + 1 + client_id_len].decode('utf-8')
                self.clients[client_id] = client
                client.send(b'\x20\x02\x00\x00')  # CONNACK with 0x00 connection accepted
                self.printD(f'Debug: Client connected: {client_id}')
                
            except ValueError as ve:
                self.printE(f'Error: Error in handle_connect: {ve}')
                # Close the client connection
                client.close()
            except Exception as e:
                self.printE(f'Error: Error in handle_connect: {e}')
                # Close the client connection
                client.close()
        else:
            client_id = random.randrange(0, 255)
            self.clients[client_id] = client
            client.send(b'\x20\x02\x00\x00')  # CONNACK with 0x00 connection accepted
    # Received message: b'\x00\x04pingstart'  -  0
    def handle_publish(self, client, msg):
        try:
            # Extract topic and payload from the message
            topic_len = struct.unpack('>H', msg[2:4])[0]
            topic = msg[4:4 + topic_len].decode('utf-8')
            payload = msg[4 + topic_len:]

            # Log the received message and topic
            self.printR(f'Recieve: Received message: {payload} on topic: {topic}')

            # Forward the message to subscribers
            if topic in self.topics:
                for subscriber in self.topics[topic]:
                    try:
                        if True:# self.is_socket_open(subscriber):
                            subscriber.send(msg)  # Forward the entire message
                        else:
                            self.printW(f'Warning: Subscriber socket closed, removing from topic: {subscriber}')
                            self.topics[topic].remove(subscriber)
                    except OSError as e:
                        self.printE(f'Error: Error forwarding message to subscriber: {e}')
                        self.printE(f'Error: Removing subscriber: {subscriber}')
                        # self.topics[topic].remove(subscriber)
            else:
                self.printW(f'Warning: No subscribers for topic: {topic}')

            self.printS(f'Publish: {payload} published to topic: {topic}')
        except Exception as e:
            self.printE(f'Error: Error in handle_publish: {e}')



    def handle_subscribe(self, client, msg):
        try:
            self.printD(f"Debug: Received subscription message: {msg}")
            topics = []
            packet_id = msg[2:4]
            index = 4
            if msg[5] == 0:
                index = index + 1

            while index < len(msg):
                # Ensure there are enough bytes to read the topic length
                if index + 2 > len(msg):
                    raise ValueError(f"Invalid message: unable to read topic length at index {index}")

                # Read the topic length
                topic_len = struct.unpack('>H', msg[index:index+2])[0]
                index += 2

                self.printD(f"Debug: Read topic length: {topic_len} at index {index - 2}")

                # Ensure there are enough bytes to read the topic
                if index + topic_len > len(msg):
                    raise ValueError(f"Invalid message: topic length exceeds message length ({topic_len} > {len(msg) - index})")

                # Extract topic string
                topic = msg[index:index + topic_len].decode('utf-8')
                index += topic_len

                self.printD(f"Debug: Read topic: {topic} at index {index - topic_len}")

                # Ensure there is a QoS byte
                if index >= len(msg):
                    raise ValueError('Invalid message: missing QoS byte')

                # Read the QoS byte
                qos = msg[index]
                index += 1

                self.printD(f"Debug: Read QoS: {qos} at index {index - 1}")

                if topic in self.topics:
                    self.topics[topic].append(client)
                else:
                    self.topics[topic] = [client]

                topics.append(topic)
                

            # Respond with a SUBACK for the first topic's packet_id (assuming single subscription)
            client.send(b'\x90\x03' + packet_id + b'\x00')  # SUBACK
            self.printR(f'Subscription: Client subscribed to topics: {topics}')

        except Exception as e:
            # Send SUBNACK message
            self.printE(f'Error: Error in handle_subscribe, Sent SUBNACK due to error: {e}')
            client.send(b'\x90\x03' + packet_id + b'\x80')


    def handle_unsubscribe(self, client, msg):
        try:
            topic_len = struct.unpack('>H', msg[4:6])[0]
            topic = msg[6:6 + topic_len].decode('utf-8')
            if topic in self.topics and client in self.topics[topic]:
                self.topics[topic].remove(client)
                if not self.topics[topic]:
                    del self.topics[topic]
            packet_id = msg[2:4]
            client.send(b'\xb0\x02' + packet_id)  # UNSUBACK
            self.printI(f'Info: Client unsubscribed from topic: {topic}')
        except Exception as e:
            self.printE(f'Error: Error in handle_unsubscribe: {e}')
            
    def handle_disconnect(self, client):
        client_id = None
        for cid, cl in self.clients.items():
            if cl == client:
                client_id = cid
                break
        if client_id:
            del self.clients[client_id]
        client.close()
        self.printW(f'Warning: Client disconnected: {client_id}')

    def send_pingresp(self, client):
        client.send(b'\xd0\x00')  # PINGRESP
        self.printD('Debug: Sent PINGRESP')

    def cleanup_clients(self):
        for client in self.clients.values():
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        gc.collect()
        
    def is_socket_open(self, client):
        try:
            # Send a dummy byte to check if the socket is still open
            client.send(b'')
            return True
        except OSError:
            return False
    
    def printD(self, text):
        if self.debug:
            print(text)
    
    def printI(self, text):
        print(self.INFO + self.BOLD + text + self.CLEAR)
    
    def printW(self, text):
        print(self.WARNING + self.BOLD + text + self.CLEAR)
    
    def printE(self, text):
        print(self.ERROR + self.BOLD + text + self.CLEAR)
        
    def printS(self, text):
        print(self.SEND + self.BOLD + text + self.CLEAR)
    
    def printR(self, text):
        print(self.RECIEVE + self.BOLD + text + self.CLEAR)
    
    def set_led(self, color):
        self.led[0] = color
        self.led.write()
    
    HEADER = '\033[95m'
    SEND = '\033[94m'
    RECIEVE = '\033[96m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CLEAR = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'