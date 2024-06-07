import network
ssid = "allan_er_nice"
my_password = "1234igen"

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=my_password)