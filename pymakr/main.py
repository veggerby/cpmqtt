from MQTTBroker import MQTTBroker
from MQTTAuthenticator import Authenticator

def main():
    host = '0.0.0.0'
    port = 1883
    rgb_led_pin = 4  # Change this according to your setup

    # Define the user database for authentication
    user_db = {
        "admin": "password",  # Replace with your desired username and password
        "user": "userpass"
    }

    # Initialize the broker
    broker = MQTTBroker(host=host, port=port, rgb_led=rgb_led_pin)
    broker.authenticator = Authenticator(user_db)

    # Start the broker
    broker.start()

if __name__ == "__main__":
    main()
