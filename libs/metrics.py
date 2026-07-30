import gc  # type: ignore
import os
import time

import esp32  # type: ignore
import machine  # type: ignore
import network  # type: ignore

_RESET_CAUSES = {
    machine.PWRON_RESET: "power-on",
    machine.HARD_RESET: "hard",
    machine.WDT_RESET: "watchdog",
    machine.DEEPSLEEP_RESET: "deepsleep",
    machine.SOFT_RESET: "soft",
}


def human_size(n):
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f}MB"
    if n >= 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n}B"


def human_uptime(ms):
    s = ms // 1000
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}h{m:02d}m{s:02d}s"


class Metrics:
    # RAM is the MicroPython gc heap, not raw SRAM; storage is the free space on
    # the filesystem partition, not raw flash.

    def __init__(self):
        self._gc_collections = 0

    def raw(self):
        block_size, _, total, free = os.statvfs("/")[:4]
        gc.collect()
        self._gc_collections += 1
        ram_free = gc.mem_free()
        ram_used = gc.mem_alloc()

        wlan = network.WLAN(network.STA_IF)
        rssi = wlan.status("rssi") if wlan.active() and wlan.isconnected() else None

        return {
            "cpu_mhz": machine.freq() // 1_000_000,
            "cpu_temp_c": esp32.mcu_temperature(),
            "ram_used": ram_used,
            "ram_total": ram_used + ram_free,
            "storage_used": (total - free) * block_size,
            "storage_total": total * block_size,
            "uptime_ms": time.ticks_ms(),
            "reset_cause": _RESET_CAUSES.get(machine.reset_cause(), "unknown"),
            "wifi_rssi": rssi,
            "gc_collections": self._gc_collections,
        }

    def formatted(self):
        m = self.raw()
        rssi = f"{m['wifi_rssi']}dBm" if m["wifi_rssi"] is not None else "n/a"
        return (
            f"CPU: {m['cpu_mhz']} MHz @ {m['cpu_temp_c']}C | "
            f"RAM: {human_size(m['ram_used'])}/{human_size(m['ram_total'])} used | "
            f"STORAGE: {human_size(m['storage_used'])}/{human_size(m['storage_total'])} used | "
            f"UP: {human_uptime(m['uptime_ms'])} | "
            f"RST: {m['reset_cause']} | "
            f"WIFI: {rssi} | "
            f"GC: {m['gc_collections']}"
        )
