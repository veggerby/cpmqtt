from machine import Pin
from time import sleep_ms, sleep

LOW = 0
HIGH = 1

CLOCKWISE = -1
COUNTER_CLOCKWISE = 1

HALF_STEP = [
    [LOW, LOW, LOW, HIGH],
    [LOW, LOW, HIGH, HIGH],
    [LOW, LOW, HIGH, LOW],
    [LOW, HIGH, HIGH, LOW],
    [LOW, HIGH, LOW, LOW],
    [HIGH, HIGH, LOW, LOW],
    [HIGH, LOW, LOW, LOW],
    [HIGH, LOW, LOW, HIGH],
]

FULL_STEP = [
    [HIGH, LOW, HIGH, LOW],
    [LOW, HIGH, HIGH, LOW],
    [LOW, HIGH, LOW, HIGH],
    [HIGH, LOW, LOW, HIGH]
]

FULL_ROTATION = int(4075.7728395061727 / 8) # http://www.jangeox.be/2013/10/stepper-motor-28byj-48_25.html

class Stepper:
    IN1: any
    IN2: any
    IN3: any
    IN4: any
    delay: any
    sequence: any

    def __init__(self, in1, in2, in3, in4, delay = 1, sequence = HALF_STEP):
        self.IN1 = Pin(in1, Pin.OUT)
        self.IN2 = Pin(in2, Pin.OUT)
        self.IN3 = Pin(in3, Pin.OUT)
        self.IN4 = Pin(in4, Pin.OUT)
        self.delay = delay
        self.sequence = sequence

    def turn(self, rotations, direction = CLOCKWISE):
        steps = FULL_ROTATION * rotations
        for _ in range(steps):
            for step in self.sequence[::direction]:
                self.IN1.value(step[0])
                self.IN2.value(step[1])
                self.IN3.value(step[2])
                self.IN4.value(step[3])
                sleep(self.delay / 1000)
        self.reset()

    def reset(self):
        self.IN1.value(LOW)
        self.IN2.value(LOW)
        self.IN3.value(LOW)
        self.IN4.value(LOW)

