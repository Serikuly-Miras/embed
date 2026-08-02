import time

from metrics import Metrics  # type: ignore

metrics = Metrics()

while True:
    time.sleep(0.1)
    print(metrics.formatted())
    time.sleep(1.9)
