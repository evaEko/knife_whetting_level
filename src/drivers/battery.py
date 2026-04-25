import machine
import struct
import uctypes
import time


def read_battery_pct():
    """Read battery % via nRF52840 internal VDDH/5 measurement (nice!nano v2)."""
    try:
        S = 0x40007000
        machine.mem32[S+0x500] = 0
        machine.mem32[S+0x510] = 13      # VDDHDIV5
        machine.mem32[S+0x514] = 0
        machine.mem32[S+0x518] = (2<<10) # gain=1/6, ref=0.6V, tacq=10us
        machine.mem32[S+0x5F0] = 2       # 12-bit
        buf = bytearray(4)
        machine.mem32[S+0x62C] = uctypes.addressof(buf)
        machine.mem32[S+0x630] = 1
        machine.mem32[S+0x500] = 1
        machine.mem32[S+0x100] = 0
        machine.mem32[S+0x104] = 0
        machine.mem32[S+0x000] = 1
        time.sleep_ms(10)
        machine.mem32[S+0x004] = 1
        time.sleep_ms(10)
        machine.mem32[S+0x500] = 0
        raw = max(0, struct.unpack('<h', buf[:2])[0])
        vddh = raw * 18.0 / 4096
        pct = (vddh - 3.2) / (4.2 - 3.2) * 100
        return max(0, min(100, int(pct)))
    except Exception as e:
        print(f"BATT ERROR: {e}")
        return None
