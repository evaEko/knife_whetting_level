import time
from states import STATE_READY
from drivers.oled import display_angle


def run(ctx, oled, raw_angle, event, update_display):
    if update_display:
        display_angle(oled, ctx['smooth_angle'], label="CAL")

    if event == 'short':
        ctx['angle_offset'] = raw_angle
        ctx['smooth_angle'] = 0.0
        print(f"-> SET offset={raw_angle:+.1f}, -> READY")
        display_angle(oled, 0.0, label="SET")
        time.sleep_ms(500)
        ctx['state'] = STATE_READY
