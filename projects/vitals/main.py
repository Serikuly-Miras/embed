import time

import machine  # type: ignore
from metrics import Metrics  # type: ignore

led = machine.Pin(8, machine.Pin.OUT)
metrics = Metrics()

while True:
    led.value(0)
    time.sleep(0.1)
    led.value(1)
    print(metrics.formatted())
    time.sleep(1.9)
