import json  # type: ignore
import time  # type: ignore

import machine  # type: ignore
import ntptime  # type: ignore
from env import (  # type: ignore
    API_HOST,
    API_PATH,
    AUTH_TOKEN,
    BOARD_ID,
    FREQUENCY,
    SLEEP_SECONDS,
    WIFI_PASSWORD,
    WIFI_SSID,
)
from https import post_json  # type: ignore
from metrics import Metrics  # type: ignore
from wifi import connect_wifi  # type: ignore

machine.freq(FREQUENCY)

start = time.ticks_ms()
metrics = Metrics()


def read_sensor():
    return metrics.raw()


connect_wifi(WIFI_SSID, WIFI_PASSWORD)
ntptime.settime()  # RTC starts unset on boot; TLS cert validity checks need real time

payload = json.dumps({"board_id": BOARD_ID, "payload": read_sensor()}).encode()

status, _ = post_json(
    API_HOST,
    API_PATH,
    payload,
    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
)
print("POST status:", status)

elapsed = time.ticks_diff(time.ticks_ms(), start)
sleep_ms = max(SLEEP_SECONDS * 1000 - elapsed, 0)
machine.deepsleep(sleep_ms)
