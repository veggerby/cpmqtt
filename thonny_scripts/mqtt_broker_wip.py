import usocket as socket
import ustruct as struct
import ubinascii as binascii
import ujson as json
import network
import time
import gc
import threading

class MQTTBroker:
    def __init__(self, host='0.0.0.0', port=1883):
        self.host = host
        self.port = port
        self.clients = {}
        self.topics = {}

    def add_client(self, client_socket):
        # Add a new client to the list of connected clients
        self.clients[client_socket] = {}

    def remove_client(self, client_socket):
        # Remove a client from the list of connected clients
        del self.clients[client_socket]

    def start(self):
        # Connect to WiFi (replace with your SSID and password)
        ssid = 'Signes_hytte_2.4GHz'
        password = '2744igen'
                       
        wifi = network.WLAN(network.STA_IF); wifi.active(True)
        wifi.scan()                             # Scan for available access points
        wifi.connect("Signes_hytte_2.4GHz", "2744igen") # Connect to an AP
        wifi.isconnected()                      # Check for successful connection
        while not wifi.isconnected():
            time.sleep(1)
        
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        s = socket.socket()
        s.bind(addr)
        s.listen(5)
        print("MQTT broker listening on {}:{}".format(wifi.ifconfig()[0], self.port))

        while True:
            try:
                cl, addr = s.accept()
                print('Client connected from', addr)
                cl.settimeout(60.0)
                self.add_client(cl)
                threading.Thread(target=self.handle_client, args=(cl,)).start()
            except Exception as e:
                print('Error:', e)
                self.cleanup_clients()

    def handle_client(self, client):
        client.settimeout(20.0)  # Increase timeout to 20 seconds
        try:
            while True:
                msg = client.recv(2048)
                if not msg:
                    print("No message received, closing connection.")
                    self.remove_client(client)
                    break
                print('Received message:', msg, ' - ', ((msg[0] & 0xF0) >> 4) )
                msg_type = (msg[0] & 0xF0) >> 4
                print('Message type:', msg_type)
                if msg_type == 1:  # CONNECT
                    self.handle_connect(client, msg)
                elif msg_type == 3:  # PUBLISH
                    self.handle_publish(client, msg)
                elif msg_type == 8:  # SUBSCRIBE
                    self.handle_subscribe(client, msg)
                elif msg_type == 10:  # UNSUBSCRIBE
                    self.handle_unsubscribe(client, msg)
                elif msg_type == 12:  # PINGREQ
                    self.send_pingresp(client)
                elif msg_type == 14:  # DISCONNECT
                    self.handle_disconnect(client)
                else:
                    print('Unknown message type:', msg_type)
        except Exception as e:
            print('Client handling error:', e)
            self.remove_client(client)
        finally:
            print('Closing client connection.')
            client.close()

    def handle_connect(self, client, msg):
        try:
            protocol_name_len = struct.unpack('>H', msg[2:4])[0]
            protocol_name = msg[4:4 + protocol_name_len].decode('utf-8')
            print('Protocol Name:', protocol_name)
            
            # Check if the protocol name is MQTT
            if protocol_name != 'MQTT':
                print('Unsupported protocol:', protocol_name)
                raise ValueError('Unsupported protocol')
            
            client_id_len = struct.unpack('>H', msg[10 + protocol_name_len + 1:12 + protocol_name_len + 1])[0]
            client_id = msg[12 + protocol_name_len + 1:12 + protocol_name_len + 1 + client_id_len].decode('utf-8')
            self.clients[client_id] = client
            client.send(b'\x20\x02\x00\x00')  # CONNACK with 0x00 connection accepted
            print('Client connected:', client_id)
            
        except ValueError as ve:
            print('Error in handle_connect:', ve)
            # Close the client connection
            client.close()
        except Exception as e:
            print('Error in handle_connect:', e)
            # Close the client connection
            client.close()

    def handle_publish(self, client, msg):
        try:
            # Extract topic and payload from the message
            topic_len = struct.unpack('>H', msg[2:4])[0]
            topic = msg[4:4 + topic_len].decode('utf-8')
            payload = msg[4 + topic_len:]

            # Log the received message and topic
            print('Received message:', payload, 'on topic:', topic)

            # Forward the message to subscribers
            if topic in self.topics:
                for subscriber in self.topics[topic]:
                    try:
                        if True:# self.is_socket_open(subscriber):
                            subscriber.send(msg)  # Forward the entire message
                        else:
                            print('Subscriber socket closed, removing from topic:', subscriber)
                            self.topics[topic].remove(subscriber)
                    except OSError as e:
                        print('Error forwarding message to subscriber:', e)
                        print('Removing subscriber:', subscriber)
                        # self.topics[topic].remove(subscriber)
            else:
                print('No subscribers for topic:', topic)

            print('Message published to topic:', topic)
        except Exception as e:
            print('Error in handle_publish:', e)



    def handle_subscribe(self, client, msg):
        try:
            print("Received subscription message:", msg)
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

                print(f"Read topic length: {topic_len} at index {index - 2}")

                # Ensure there are enough bytes to read the topic
                if index + topic_len > len(msg):
                    raise ValueError(f"Invalid message: topic length exceeds message length ({topic_len} > {len(msg) - index})")

                # Extract topic string
                topic = msg[index:index + topic_len].decode('utf-8')
                index += topic_len

                print(f"Read topic: {topic} at index {index - topic_len}")

                # Ensure there is a QoS byte
                if index >= len(msg):
                    raise ValueError('Invalid message: missing QoS byte')

                # Read the QoS byte
                qos = msg[index]
                index += 1

                print(f"Read QoS: {qos} at index {index - 1}")

                if topic in self.topics:
                    self.topics[topic].append(client)
                else:
                    self.topics[topic] = [client]

                topics.append(topic)
                

            # Respond with a SUBACK for the first topic's packet_id (assuming single subscription)
            client.send(b'\x90\x03' + packet_id + b'\x00')  # SUBACK
            print('Client subscribed to topics:', topics)

        except Exception as e:
            # Send SUBNACK message
            print('Error in handle_subscribe, Sent SUBNACK due to error:', e)
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
            print('Client unsubscribed from topic:', topic)
        except Exception as e:
            print('Error in handle_unsubscribe:', e)
            
    def handle_disconnect(self, client):
        client_id = None
        for cid, cl in self.clients.items():
            if cl == client:
                client_id = cid
                break
        if client_id:
            del self.clients[client_id]
        client.close()
        print('Client disconnected:', client_id)

    def send_pingresp(self, client):
        client.send(b'\xd0\x00')  # PINGRESP
        print('Sent PINGRESP')

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

broker = MQTTBroker()
broker.start()