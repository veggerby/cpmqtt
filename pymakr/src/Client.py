from Logger import Logger

class ClientSettings:
    client_id: any
    protocol_name: any
    protocol_version: any
    connect_flags: any
    keep_alive: any

    def __init__(self, client_id, protocol_name, protocol_version, connect_flags, keep_alive):
        self.client_id = client_id
        self.protocol_name = protocol_name
        self.protocol_version = protocol_version
        self.connect_flags = connect_flags
        self.keep_alive = keep_alive

class Client:
    client_name: str = ''
    client_settings: ClientSettings = None
    logger: Logger = None

    def __init__(self, client_name: str, client_settings: ClientSettings, logger: Logger = None):
        self.client_name = client_name
        self.client_settings = client_settings
        self.logger = logger or Logger()

    def is_ready(self):
        raise NotImplementedError

    def send(self, msg: bytes):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
