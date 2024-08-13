# boot.py -- run on boot-up
import sys  # pylint: disable=wrong-import-position
# from wifi import try_connect_to_wifi
from wifi import start_hotspot

sys.path.insert(1, '/src')

start_hotspot()
