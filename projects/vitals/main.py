import gc  # type: ignore
import os
import time

import machine  # type: ignore

led = machine.Pin(8, machine.Pin.OUT)


def human_size(n):
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f}MB"
    if n >= 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n}B"


def print_metrics():
    # RAM is the MicroPython gc heap, not raw SRAM; storage is the free space on
    # the filesystem partition, not raw flash.
    block_size, _, total, free = os.statvfs("/")[:4]
    storage_used = (total - free) * block_size
    storage_total = total * block_size

    gc.collect()
    ram_free = gc.mem_free()
    ram_used = gc.mem_alloc()

    cpu_mhz = machine.freq() // 1_000_000
    ram_total = ram_used + ram_free
    print(
        f"CPU: {cpu_mhz} MHz | RAM: {human_size(ram_used)}/{human_size(ram_total)} used | "
        f"Storage: {human_size(storage_used)}/{human_size(storage_total)} used"
    )


while True:
    led.value(0)
    time.sleep(0.1)
    led.value(1)
    print_metrics()
    time.sleep(1.9)
