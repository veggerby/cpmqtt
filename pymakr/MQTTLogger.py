class MQTTLogger:
    HEADER = '\033[95m'
    SEND = '\033[94m'
    RECEIVE = '\033[96m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CLEAR = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def debug(message, debug):
        if debug:
            print(f'{MQTTLogger.HEADER}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def info(message, debug):
        if debug:
            print(f'{MQTTLogger.INFO}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def warning(message, debug):
        if debug:
            print(f'{MQTTLogger.WARNING}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def error(message, debug):
        if debug:
            print(f'{MQTTLogger.ERROR}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def send(message, debug):
        if debug:
            print(f'{MQTTLogger.SEND}{message}{MQTTLogger.CLEAR}')

    @staticmethod
    def receive(message, debug):
        if debug:
            print(f'{MQTTLogger.RECEIVE}{message}{MQTTLogger.CLEAR}')
