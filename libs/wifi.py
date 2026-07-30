import time

import network  # type: ignore


def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                raise RuntimeError("Wi-Fi connection timed out")
            time.sleep(0.5)
    wlan.config(pm=network.WLAN.PM_NONE)  # disable modem-sleep; cuts request latency a lot
    print("Wi-Fi connected, IP:", wlan.ifconfig()[0])
    return wlan
