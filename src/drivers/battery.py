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


def usb_connected():
    """True if USB VBUS is present."""
    return bool(machine.mem32[0x40000438] & 0x01)


def _saadc_raw(psel, gain):
    """One 12-bit oversampled SAADC conversion of channel input `psel`.
    tacq=40us: required for the internal VDDHDIV5 divider and for the
    ~570k source resistance of the v1 battery divider."""
    S = 0x40007000
    machine.mem32[S+0x500] = 0
    machine.mem32[S+0x510] = psel
    machine.mem32[S+0x514] = 0
    machine.mem32[S+0x518] = (gain<<8) | (5<<16) | (1<<24)  # tacq=40us, burst=1
    machine.mem32[S+0x5F0] = 2        # 12-bit
    machine.mem32[S+0x5F4] = 4        # oversample 16x (2^4)
    buf = bytearray(4)
    machine.mem32[S+0x62C] = uctypes.addressof(buf)
    machine.mem32[S+0x630] = 1
    machine.mem32[S+0x500] = 1
    machine.mem32[S+0x100] = 0
    machine.mem32[S+0x104] = 0
    machine.mem32[S+0x000] = 1
    time.sleep_ms(20)
    machine.mem32[S+0x004] = 1
    time.sleep_ms(20)
    machine.mem32[S+0x500] = 0
    return max(0, struct.unpack('<h', buf[:2])[0])


def _battery_mv():
    """Battery voltage in mV; picks the measurement path per board design.
    POWER->MAINREGSTATUS bit 0 tells which power circuit the board has:
    1 = high voltage mode (nice!nano v2: battery feeds VDDH directly),
    0 = normal mode (nice!nano v1 / clones: external 3.3V LDO, battery
        sensed through the on-board 806k/2M divider on P0.04/AIN2)."""
    if machine.mem32[0x40000640] & 0x01:
        # VDDHDIV5, gain=1/2, ref=0.6V: full-scale 1.2V; ×5 → VDDH
        return _saadc_raw(13, 4) * 6000 // 4096
    # AIN2, gain=1/6: full-scale 3.6V; divider ratio 2M/(2M+806k)
    return _saadc_raw(3, 0) * 3600 * 2806 // (4096 * 2000)


def read_battery_pct():
    """Read battery % (nice!nano v1/v2 and compatibles)."""
    try:
        mv = _battery_mv()
        # USB without battery: VDDH sees raw USB voltage, ~4.46V (above the
        # charger's 4.2V regulated maximum). Battery connected clamps the
        # measured voltage to ≤4.2V. Threshold at 4300mV separates the two.
        if usb_connected() and mv > 4300:
            return None
        return _mv_to_pct(max(3300, min(4200, mv)))
    except Exception as e:
        print(f"BATT ERROR: {e}")
        return None
