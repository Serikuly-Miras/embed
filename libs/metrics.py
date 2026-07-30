import gc  # type: ignore
import os

import machine  # type: ignore


def human_size(n):
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f}MB"
    if n >= 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n}B"


class Metrics:
    # RAM is the MicroPython gc heap, not raw SRAM; storage is the free space on
    # the filesystem partition, not raw flash.

    def raw(self):
        block_size, _, total, free = os.statvfs("/")[:4]
        gc.collect()
        ram_free = gc.mem_free()
        ram_used = gc.mem_alloc()

        return {
            "cpu_mhz": machine.freq() // 1_000_000,
            "ram_used": ram_used,
            "ram_total": ram_used + ram_free,
            "storage_used": (total - free) * block_size,
            "storage_total": total * block_size,
        }

    def formatted(self):
        m = self.raw()
        return (
            f"CPU: {m['cpu_mhz']} MHz | "
            f"RAM: {human_size(m['ram_used'])}/{human_size(m['ram_total'])} used | "
            f"Storage: {human_size(m['storage_used'])}/{human_size(m['storage_total'])} used"
        )
