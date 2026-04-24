import time
import ctx
from config import SMOOTHING, DEVIATION_THRESHOLD
from drivers.oled import display_angle

IDLE_TIMEOUT       = 60_000
MOVEMENT_THRESHOLD = 0.5
DISPLAY_INTERVAL   = 50

_imu_idle       = False
_last_movement  = 0
_idle_ref_angle = 0.0
_last_display   = 0


def measure():
    global _imu_idle, _last_movement, _idle_ref_angle, _last_display

    if ctx.imu is None:
        time.sleep_ms(10)
        return None

    try:
        ctx.imu.update()
        ctx.raw_angle = ctx.imu.get_pitch()
        angle = ctx.raw_angle - ctx.angle_offset
        while angle > 180.0:  angle -= 360.0
        while angle < -180.0: angle += 360.0
        if abs(angle - ctx.smooth_angle) > 180.0:
            ctx.smooth_angle = angle
        else:
            ctx.smooth_angle = SMOOTHING * ctx.smooth_angle + (1.0 - SMOOTHING) * angle
    except OSError:
        time.sleep_ms(5)
        return None

    now = time.ticks_ms()

    if abs(ctx.smooth_angle - _idle_ref_angle) >= MOVEMENT_THRESHOLD:
        _idle_ref_angle = ctx.smooth_angle
        _last_movement = now
        if _imu_idle:
            ctx.imu.set_report_interval(10)
            _imu_idle = False
    elif not _imu_idle and time.ticks_diff(now, _last_movement) >= IDLE_TIMEOUT:
        ctx.imu.set_report_interval(1000)
        _imu_idle = True

    if time.ticks_diff(now, _last_display) >= DISPLAY_INTERVAL:
        _last_display = now
        angle_offset = ctx.angle_offset
        if angle_offset != 0.0:
            near_zero   = abs(ctx.smooth_angle) <= DEVIATION_THRESHOLD
            near_mirror = abs(ctx.smooth_angle + 2 * angle_offset) <= DEVIATION_THRESHOLD
            ctx.oled.invert(not (near_zero or near_mirror))
        display_angle(ctx.oled, ctx.smooth_angle)

    ev_low = ctx.btn_low.update() if ctx.btn_low else None
    ev_top = ctx.btn_top.update() if ctx.btn_top else None
    if ev_low:
        return (ev_low, 'low')
    if ev_top:
        return (ev_top, 'top')
    return None
