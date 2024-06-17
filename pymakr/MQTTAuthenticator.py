from MQTTLogger import Logger

class Authenticator:
    def __init__(self, user_db, logger = None):
        self.user_db = user_db
        self.logger = logger or Logger()

    def authenticate(self, username, password):
        self.logger.info(f'Authenticating user: {username}')
        return self.user_db.get(username) == password
