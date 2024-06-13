class Authenticator:
    def __init__(self, user_db):
        self.user_db = user_db

    def authenticate(self, username, password):
        return self.user_db.get(username) == password
