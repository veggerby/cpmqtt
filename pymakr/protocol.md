# MQTT Message Types and Their Structures

See <https://cedalo.com/blog/mqtt-packet-guide/>

## 1. CONNECT Message (Type 1)

**Header: message type: 1**

1. **Protocol Name**
   - **Offset**: 2
   - **Key**: `protocol_name`
   - **Type**: string
   - **Format**: UTF-8 encoded string
   - **Description**: Name of the protocol (usually "MQTT")
   - **Read**:

     ```python
     protocol_name, offset = self.__read_string(msg, 2)
     ```

2. **Protocol Version**
   - **Offset**: Varies (depends on `protocol_name` length)
   - **Key**: `protocol_version`
   - **Type**: byte
   - **Description**: Version of the MQTT protocol
   - **Read**:

     ```python
     protocol_version, offset = self.__read_byte(msg, offset)
     ```

3. **Connect Flags**
   - **Offset**: Varies (depends on previous fields)
   - **Key**: `connect_flags`
   - **Type**: byte
   - **Description**: Flags indicating connection options (username, password, will, clean session)
   - **Read**:

     ```python
     connect_flags, offset = self.__read_byte(msg, offset)
     ```

4. **Keep Alive**
   - **Offset**: Varies (depends on previous fields)
   - **Key**: `keep_alive`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Maximum time interval between messages
   - **Read**:

     ```python
     keep_alive, offset = self.__read_short(msg, offset)
     ```

5. **Client ID**
   - **Offset**: Varies (depends on previous fields)
   - **Key**: `client_id`
   - **Type**: string
   - **Format**: UTF-8 encoded string
   - **Description**: Unique identifier for the client
   - **Read**:

     ```python
     client_id, offset = self.__read_string(msg, offset)
     ```

6. **Username (optional)**
   - **Offset**: Varies (depends on previous fields)
   - **Key**: `username`
   - **Type**: string
   - **Format**: UTF-8 encoded string
   - **Description**: Username for authentication
   - **Read**:

     ```python
     if connect_flags & 0x80:
         username, offset = self.__read_string(msg, offset)
     ```

7. **Password (optional)**
   - **Offset**: Varies (depends on previous fields)
   - **Key**: `password`
   - **Type**: string
   - **Format**: UTF-8 encoded string
   - **Description**: Password for authentication
   - **Read**:

     ```python
     if connect_flags & 0x40:
         password, offset = self.__read_string(msg, offset)
     ```

## 2. CONNACK Message (Type 2)

**Header: message type: 2**

1. **Connect Acknowledge Flags**
   - **Offset**: 2
   - **Key**: `ack_flags`
   - **Type**: byte
   - **Description**: Acknowledgment flags
   - **Read**:

     ```python
     ack_flags, offset = self.__read_byte(msg, 2)
     ```

2. **Connect Return Code**
   - **Offset**: 3
   - **Key**: `return_code`
   - **Type**: byte
   - **Description**: Return code indicating the status of the connection request
   - **Read**:

     ```python
     return_code, offset = self.__read_byte(msg, 3)
     ```

## 3. PUBLISH Message (Type 3)

**Header: message type: 3**

1. **Fixed Header**
   - **Offset**: 0
   - **Key**: `fixed_header`
   - **Type**: byte
   - **Description**: Contains message type and flags
   - **Read**:

     ```python
     fixed_header, offset = self.__read_byte(msg, 0)
     ```

2. **Remaining Length**
   - **Offset**: 1
   - **Key**: `remaining_length`
   - **Type**: byte
   - **Description**: Length of the remaining part of the message
   - **Read**:

     ```python
     remaining_length, offset = self.__read_byte(msg, 1)
     ```

3. **Topic Name**
   - **Offset**: Varies
   - **Key**: `topic_name`
   - **Type**: string
   - **Format**: UTF-8 encoded string
   - **Description**: Topic to which the message is published
   - **Read**:

     ```python
     topic_name, offset = self.__read_string(msg, offset)
     ```

4. **Packet Identifier (if QoS > 0)**
   - **Offset**: Varies
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the packet
   - **Read**:

     ```python
     if qos_level > 0:
         packet_id, offset = self.__read_short(msg, offset)
     ```

5. **Payload**
   - **Offset**: Varies
   - **Key**: `payload`
   - **Type**: bytes
   - **Format**: Raw bytes
   - **Description**: The actual message content
   - **Read**:

     ```python
     payload, offset = self.__read(msg, offset, remaining_length - (offset - 2))
     ```

## 4. PUBACK Message (Type 4)

**Header: message type: 4**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the acknowledged packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

## 5. PUBREC Message (Type 5)

**Header: message type: 5**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the received packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

## 6. PUBREL Message (Type 6)

**Header: message type: 6**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the released packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

## 7. PUBCOMP Message (Type 7)

**Header: message type: 7**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the completed packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

## 8. SUBSCRIBE Message (Type 8)

**Header: message type: 8**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the subscription packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

2. **Topic Filters and QoS**
   - **Offset**: Varies
   - **Key**: `topics`
   - **Type**: list of tuples
   - **Format**: UTF-8 encoded string (topic) and byte (QoS)
   - **Description**: List of topics and corresponding QoS levels
   - **Read**:

     ```python
     topics = []
     while offset < len(msg):
         topic, offset = self.__read_string(msg, offset)
         qos, offset = self.__read_byte(msg, offset)
         topics.append((topic, qos))
     ```

## 9. SUBACK Message (Type 9)

**Header: message type: 9**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the subscription acknowledgment packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

2. **Return Codes**
   - **Offset**: Varies
   - **Key**: `return_codes`
   - **Type**: list of bytes
   - **Format**: Byte
   - **Description**: List of return codes for each topic
   - **Read**:

     ```python
     return_codes = []
     while offset < len(msg):
         return_code, offset = self.__read_byte(msg, offset)
         return_codes.append(return_code)
     ```

## 10. UNSUBSCRIBE Message (Type 10)

**Header: message type: 10**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the unsubscription packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

2. **Topic Filters**
   - **Offset**: Varies
   - **Key**: `topics`
   - **Type**: list of strings
   - **Format**: UTF-8 encoded strings
   - **Description**: List of topics to unsubscribe from
   - **Read**:

     ```python
     topics = []
     while offset < len(msg):
         topic, offset = self.__read_string(msg, offset)
         topics.append(topic)
     ```

## 11. UNSUBACK Message (Type 11)

**Header: message type: 11**

1. **Packet Identifier**
   - **Offset**: 2
   - **Key**: `packet_id`
   - **Type**: int
   - **Format**: Unsigned short
   - **Description**: Identifier for the unsubscription acknowledgment packet
   - **Read**:

     ```python
     packet_id, offset = self.__read_short(msg, 2)
     ```

## 12. PINGREQ Message (Type 12)

**Header: message type: 12**

- No additional fields, only the fixed header.

## 13. PINGRESP Message (Type 13)

**Header: message type: 13**

- No additional fields, only the fixed header.

## 14. DISCONNECT Message (Type 14)

**Header: message type: 14**

- No additional fields, only the fixed header.
