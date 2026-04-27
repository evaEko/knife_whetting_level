import time
import ctx
from drivers.battery import read_battery_pct
from drivers.oled import display_battery


def wait_for_retry():
    """Loop until battery is detected or user bypasses with low button.
    Returns the battery pct if detected, None if bypassed."""
    _t = 0
    while True:
        time.sleep_ms(50)
        if ctx.btn_low and ctx.btn_low.is_pressed():
            return None
        _t += 50
        if _t >= 500:
            _t = 0
            pct = read_battery_pct()
            if pct is not None:
                display_battery(ctx.oled, pct)
                return pct
