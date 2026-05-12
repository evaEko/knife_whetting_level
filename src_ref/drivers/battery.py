import machine
import struct
import uctypes
import time

# LiPo discharge curve (millivolts → percentage).
# Matches the actual nonlinear discharge shape rather than a straight line.
_CURVE = [
    (4200, 100), (4100, 95), (4000, 88), (3900, 79),
    (3800, 67),  (3700, 52), (3600, 36), (3500, 20),
    (3450, 10),  (3400, 5),  (3350, 2),  (3300, 0),
]


def _mv_to_pct(mv):
    for i, (v, p) in enumerate(_CURVE):
        if mv >= v:
            if i == 0:
                return 100
            v_hi, p_hi = _CURVE[i - 1]
            v_lo, p_lo = v, p
            return p_lo + (mv - v_lo) * (p_hi - p_lo) // (v_hi - v_lo)
    return 0


def read_battery_pct():
    """Read battery % via nRF52840 internal VDDH/5 measurement (nice!nano v2)."""
    try:
        S = 0x40007000
        machine.mem32[S+0x500] = 0
        machine.mem32[S+0x510] = 13       # VDDHDIV5
        machine.mem32[S+0x514] = 0
        machine.mem32[S+0x518] = (4<<8)   # gain=1/2, ref=0.6V, tacq=10us
        machine.mem32[S+0x5F0] = 2        # 12-bit
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
        # gain=1/2, ref=0.6V: full-scale input = 1.2V; VDDHDIV5 × 5 → VDDH
        mv = int(raw * 6000 / 4096)
        # USB without battery: raw USB voltage reaches ~4.46V (above the charger's
        # 4.2V regulated maximum). Battery connected clamps VDDH to ≤4.2V.
        # Threshold at 4300mV cleanly separates the two cases.
        vbus = machine.mem32[0x40000438] & 0x01
        if vbus and mv > 4300:
            return None
        return _mv_to_pct(max(3300, min(4200, mv)))
    except Exception as e:
        print(f"BATT ERROR: {e}")
        return None
