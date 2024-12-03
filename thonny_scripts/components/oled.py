from machine import Pin, I2C
import ssd1306

class OLED:
    i2c: any = None
    oled: any = None
    width: any
    height: any

    def __init__(self, scl, sda, id = 0, width = 128, height = 64):
        self.i2c = I2C(id, scl=Pin(scl), sda=Pin(sda))

        self.width = width
        self.height = height
        self.oled = ssd1306.SSD1306_I2C(self.width, self.height, self.i2c)

    def apply(self):
        self.oled.show()

    def clear(self):
        self.oled.fill(0)
        self.apply()

    def write(self, txt, x = 0, y = 0):
        self.oled.fill(0)
        self.oled.text(txt, x, y)
        self.apply()
