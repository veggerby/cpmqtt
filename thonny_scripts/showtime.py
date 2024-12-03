from machine import Pin, I2C
import ssd1306
from led import LED, RED, BLUE, GREEN
from oled import OLED
from time import sleep
from stepper import Stepper, HALF_STEP, FULL_STEP

oled = OLED(scl=6, sda=5)
oled.clear()

ledstrip = LED(10, 30)

onboard_led = LED()

count = 0

colors = [RED, BLUE, GREEN]
color = 0

stepper = Stepper(7, 15, 16, 17, delay = 1, sequence = HALF_STEP)

try:
    while True:
        stepper.turn(1)
        ledstrip.all(colors[color])
        onboard_led.on()
        sleep(1)
        onboard_led.off()
        sleep(1)
        oled.write(f"Count {count}")
        count += 1

        color = (color + 1) % len(colors)

except:
    ledstrip.off()
    onboard_led.off()
