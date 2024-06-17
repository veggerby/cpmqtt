class Logger:
    HEADER = '\033[95m'
    SEND = '\033[94m'
    RECEIVE = '\033[96m'
    INFO = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CLEAR = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    debug = True

    def __init__(self, debug) -> None:
        self.debug = debug

    def log(self, flags, message):
        if self.debug:
            print(f'{flags}{message}{Logger.CLEAR}')

    def debug(self, message):
        self.log(Logger.HEADER, message)

    def info(self, message):
        self.log(Logger.INFO, message)

    def warning(self, message):
        self.log(Logger.WARNING, message)

    def error(self, message):
        self.log(Logger.ERROR, message)

    def send(self, message):
        self.log(Logger.SEND, message)

    def receive(self, message):
        self.log(Logger.RECEIVE, message)
