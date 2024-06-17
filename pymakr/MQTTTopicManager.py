import MQTTLogger as Logger

class TopicManager:
    def __init__(self, logger = None):
        self.topics = {}
        self.logger = logger or Logger()

    def subscribe(self, topic, client):
        if topic not in self.topics:
            self.topics[topic] = []
        self.topics[topic].append(client)

    def unsubscribe(self, topic, client):
        if topic in self.topics:
            self.topics[topic].remove(client)
            if not self.topics[topic]:
                del self.topics[topic]

    def publish(self, topic, msg):
        if topic in self.topics:
            for subscriber in self.topics[topic]:
                try:
                    subscriber.send(msg)
                except OSError as e:
                    self.logger.error(f'Error forwarding message to subscriber: {e}')
                    self.topics[topic].remove(subscriber)
        else:
            self.logger.warning(f'No subscribers for topic: {topic}')
