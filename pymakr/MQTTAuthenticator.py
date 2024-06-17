from MQTTLogger import Logger

class Authenticator:
    logger: Logger

    def __init__(self, user_db, logger: Logger = None):
        self.user_db = user_db
        self.logger = logger or Logger()

    def authenticate(self, username, password):
        self.logger.info(f'Authenticating user: {username}')
        return self.user_db.get(username) == password
