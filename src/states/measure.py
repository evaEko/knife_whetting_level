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
_both_start     = None


def measure():
    global _imu_idle, _last_movement, _idle_ref_angle, _last_display, _both_start

    imu_ok = False
    if ctx.imu is not None:
        try:
            ctx.imu.update()
            ctx.raw_angle = ctx.imu.get_pitch()
            # smooth_angle is relative to calibrated_offset so display shows
            # 0 at calibration point and target_angle at the correct sharpening angle
            angle = ctx.raw_angle - ctx.board_offset - ctx.calibrated_offset
            while angle > 180.0:  angle -= 360.0
            while angle < -180.0: angle += 360.0
            if abs(angle - ctx.smooth_angle) > 180.0:
                ctx.smooth_angle = angle
            else:
                ctx.smooth_angle = SMOOTHING * ctx.smooth_angle + (1.0 - SMOOTHING) * angle
            imu_ok = True
        except OSError:
            time.sleep_ms(5)

    now = time.ticks_ms()

    if imu_ok:
        if abs(ctx.smooth_angle - _idle_ref_angle) >= MOVEMENT_THRESHOLD:
            _idle_ref_angle = ctx.smooth_angle
            _last_movement = now
            if _imu_idle:
                ctx.imu.set_report_interval(10)
                _imu_idle = False
        elif not _imu_idle and time.ticks_diff(now, _last_movement) >= IDLE_TIMEOUT:
            ctx.imu.set_report_interval(1000)
            _imu_idle = True

    if ctx.oled and time.ticks_diff(now, _last_display) >= DISPLAY_INTERVAL:
        _last_display = now
        if ctx.target_angle != 0.0:
            near_target = abs(ctx.smooth_angle - ctx.target_angle) <= DEVIATION_THRESHOLD
            near_mirror = abs(ctx.smooth_angle + ctx.target_angle) <= DEVIATION_THRESHOLD
            ctx.oled.invert(not (near_target or near_mirror))
        display_angle(ctx.oled, ctx.smooth_angle, fmt=ctx.angle_format)

    # Simultaneous both-button short press → flash mode
    both_now = (ctx.btn_low and ctx.btn_low.is_pressed() and
                ctx.btn_top and ctx.btn_top.is_pressed())
    if both_now:
        if _both_start is None:
            _both_start = time.ticks_ms()
        return None  # consume individual events while both held
    elif _both_start is not None:
        from config import LONG_PRESS_MS
        duration = time.ticks_diff(time.ticks_ms(), _both_start)
        _both_start = None
        # drain any pending individual events so they don't fire after
        if ctx.btn_low: ctx.btn_low.update()
        if ctx.btn_top: ctx.btn_top.update()
        if duration < LONG_PRESS_MS:
            return ('short', 'both')

    ev_low = ctx.btn_low.update() if ctx.btn_low else None
    ev_top = ctx.btn_top.update() if ctx.btn_top else None
    if ev_low:
        return (ev_low, 'low')
    if ev_top:
        return (ev_top, 'top')
    return None
