import time
from state import State

_CUSTOM = 0


class SelectAngleState(State):
    _index = 0  # class-level: persists across visits

    def __init__(self):
        self._n          = 0
        self._clear      = 0
        self._total      = 0
        self._capturing  = False
        self._capture_at = None
        self._last_draw  = 0
        self._done_at    = None

    def enter(self, device):
        presets = device.presets
        if presets.empty:
            return
        self._n     = len(presets)
        self._clear = self._n + 1
        self._total = self._n + 2
        if SelectAngleState._index >= self._total:
            SelectAngleState._index = 0
        device.display.invert(False)
        self._show(device.display, device.engine, presets)

    def update(self, device):
        display = device.display
        engine  = device.engine
        buttons = device.buttons
        sensor  = device.sensor
        presets = device.presets

        if presets.empty:
            from states.measure import MeasureState
            return MeasureState()

        if self._done_at is not None:
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                from states.measure import MeasureState
                return MeasureState()
            return None

        if self._capturing:
            raw = sensor.update()
            if raw is not None:
                engine.update(raw)
            now = time.ticks_ms()
            remaining_ms = time.ticks_diff(self._capture_at, now)
            auto_capture = remaining_ms <= 0
            if time.ticks_diff(now, self._last_draw) >= 50:
                self._last_draw = now
                secs = max(0, (remaining_ms + 999) // 1000)
                display.show_angle(engine.smooth_angle,
                                   label=f"set:{secs}s" if not auto_capture else "set:0s",
                                   fmt=engine.angle_format)
            event = buttons.update()
            if auto_capture or event == ('short', 'low'):
                angle = abs(engine.smooth_angle)
                engine.set_target(angle, name="Custom")
                device.settings.target_angle = angle
                device.settings.save()
                print(f"-> CUSTOM {angle:.2f}°")
                if device.ble is not None and device.ble.connected:
                    device.ble.send_target_state(device)
                display.show_set_confirmation(angle, engine.angle_format)
                self._capturing  = False
                self._capture_at = None
                self._done_at = time.ticks_add(time.ticks_ms(), 1000)
            elif not auto_capture and event is not None:
                self._capturing  = False
                self._capture_at = None
                from states.measure import MeasureState
                return MeasureState()
            return None

        event = buttons.update()
        if event == ('short', 'top'):
            SelectAngleState._index = (SelectAngleState._index + 1) % self._total
            self._show(display, engine, presets)

        elif event == ('short', 'low'):
            idx = SelectAngleState._index
            if idx == _CUSTOM:
                buttons.wait_release('low')
                self._capturing  = True
                self._capture_at = time.ticks_add(time.ticks_ms(), 5000)
                self._last_draw  = 0
                display.invert(False)
            elif idx < self._clear:
                name, angle = presets[idx - 1]
                angle = abs(angle)
                engine.set_target(angle, name=name)
                device.settings.target_angle = angle
                device.settings.save()
                print(f"-> PRESET '{name}' {angle}°")
                if device.ble is not None and device.ble.connected:
                    device.ble.send_target_state(device)
                display.show_set_confirmation(angle, engine.angle_format, name=name)
                self._done_at = time.ticks_add(time.ticks_ms(), 1000)
            else:
                engine.clear_target()
                device.settings.target_angle = 0.0
                device.settings.save()
                print("-> PRESET cleared")
                if device.ble is not None and device.ble.connected:
                    device.ble.send_target_state(device)
                display.show_cleared()
                self._done_at = time.ticks_add(time.ticks_ms(), 1000)

        elif event is not None:
            from states.measure import MeasureState
            return MeasureState()

        return None

    def _show(self, display, engine, presets):
        idx = SelectAngleState._index
        if idx == _CUSTOM:
            display.show_custom()
        elif idx < self._clear:
            name, angle = presets[idx - 1]
            display.show_preset(name, angle)
        else:
            display.show_clear(engine.target_angle, engine.angle_format)
