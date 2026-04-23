from states import STATE_CALIBRATION
from config import DEVIATION_THRESHOLD
from oled import display_angle


def run(ctx, oled, event, update_display):
    smooth_angle  = ctx['smooth_angle']
    angle_offset  = ctx['angle_offset']

    if angle_offset != 0.0:
        near_zero   = abs(smooth_angle) <= DEVIATION_THRESHOLD
        near_mirror = abs(smooth_angle + 2 * angle_offset) <= DEVIATION_THRESHOLD
        oled.invert(not (near_zero or near_mirror))

    if update_display:
        display_angle(oled, smooth_angle)

    if event == 'short':
        print("-> CALIBRATION")
        ctx['state'] = STATE_CALIBRATION
        oled.invert(False)
