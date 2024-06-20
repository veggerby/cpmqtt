# boot.py -- run on boot-up
import sys  # pylint: disable=wrong-import-position
from wifi import try_connect_to_wifi

sys.path.insert(1, '/src')

try_connect_to_wifi()
