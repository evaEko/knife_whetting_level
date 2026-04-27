import time
import ctx
from drivers.battery import read_battery_pct
from drivers.oled import display_battery
from wait_for_retry import wait_for_retry


def check_battery():
    if not ctx.oled:
        return
    pct = read_battery_pct()
    display_battery(ctx.oled, pct)
    if pct is None:
        pct = wait_for_retry()
    if pct is not None:
        time.sleep_ms(1000)
