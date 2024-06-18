import traceback
import MQTTLogger as Logger
from MQTTClient import Client
from MQTTMessage import PublishMessage

class Subscription:
    topic: str = ''
    client: Client = None

    def __init__(self, topic, client):
        self.topic = topic
        self.client = client

    @staticmethod
    def __match_subscription(subscription, topic):
        """
        Check if a given MQTT topic matches a subscription topic that may contain wildcards.

        Parameters:
        - subscription (str): The subscription topic with wildcards.
        - topic (str): The topic to check against the subscription.

        Returns:
        - bool: True if the topic matches the subscription, False otherwise.
        """
        subscription_parts = subscription.split('/')
        topic_parts = topic.split('/')

        for i, sub_part in enumerate(subscription_parts):
            if sub_part == '#':
                # The # wildcard matches any remaining topic levels
                return True
            elif sub_part == '+':
                # The + wildcard matches exactly one topic level
                if i >= len(topic_parts):
                    return False
            else:
                if i >= len(topic_parts) or sub_part != topic_parts[i]:
                    return False

        # If there are more parts in the topic than in the subscription, return False
        if len(topic_parts) > len(subscription_parts):
            return False

        return True


    def is_for_topic(self, topic):
        return Subscription.__match_subscription(self.topic, topic)

# print(match_subscription('home/+/temperature', 'home/livingroom/temperature'))  # True
# print(match_subscription('home/+/temperature', 'home/livingroom/humidity'))    # False
# print(match_subscription('home/#', 'home/livingroom/temperature'))            # True
# print(match_subscription('home/#', 'home'))                                   # True
# print(match_subscription('home/+/+', 'home/livingroom/temperature'))          # True
# print(match_subscription('home/+/+', 'home/livingroom/temperature/extra'))    # False
# print(match_subscription('home/+/temperature', 'home/+/temperature'))         # False
# print(match_subscription('home/+/temperature/#', 'home/livingroom/temperature/extra'))  # True

class SubscriberManager:
    def __init__(self, logger = None):
        self.subscriptions = []
        self.logger = logger or Logger()

    def subscribe(self, topic, client):
        subscription = Subscription(topic, client)
        self.subscriptions.append(subscription)

    def unsubscribe(self, topic, client):
        for subscription in self.subscriptions:
            if subscription.is_for_topic(topic) and subscription.client == client:
                self.subscriptions.remove(subscription)

    def publish(self, topic, publish_message: PublishMessage):
        for subscription in self.subscriptions:
            if subscription.is_for_topic(topic):
                client = subscription.client
                try:
                    publish_message.send_to(client, True)
                except OSError as e:
                    self.logger.error(f'Error forwarding message to subscriber: {e}, {traceback.format_exc()}')
                    self.unsubscribe(subscription.topic, client)
