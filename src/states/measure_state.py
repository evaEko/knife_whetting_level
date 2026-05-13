from core.state import State


class MeasureState(State):
    def enter(self, app):
        app.logging.log("[MeasureState] enter")
        if not app.calibration.has_stone():
            app.display.show_text("No calibration", "", "top=calib.", "low=sett")

    def update(self, app):
        if not app.calibration.has_stone():
            return self._update_uncalibrated(app)
        return self._update_calibrated(app)

    def exit(self, app):
        app.display.invert(False)
        app.logging.log("[MeasureState] exit")

    def _update_uncalibrated(self, app):
        if app.button_event == 'short_top':
            from states.settings_handlers.surface_level_handler import SurfaceLevelHandler
            from states.settings_state import SettingsState
            handler = SurfaceLevelHandler(
                storage_key='n_stone',
                prompt=("Lay blade", "flat on stone", "top=esc", "low=capt"),
                saved_msg="Calibrated",
                on_save=app.calibration.set_stone,
            )
            return SettingsState(app.settings_items, active_handler=handler)
        if app.button_event == 'short_low':
            from states.settings_state import SettingsState
            return SettingsState(app.settings_items)
        app.ble_handler.tick()
        return None

    def _update_calibrated(self, app):
        if app.button_event == 'short_top':
            from states.angle_select_state import AngleSelectState
            return AngleSelectState(app.build_angle_items())
        if app.button_event == 'short_low':
            from states.settings_state import SettingsState
            return SettingsState(app.settings_items)
        app.measure.update()
        app.ble_handler.tick()
        self._render(app)
        return None

    def _render(self, app):
        pitch = app.measure.pitch()
        target = app.calibration.target_angle()
        has_t = app.calibration.has_target()
        in_pos = app.measure.in_position()
        target_str = "{:.1f}".format(target) if target is not None else None
        app.logging.log("pitch={:.2f} target={} has_target={} in_pos={}".format(
            pitch, target, has_t, in_pos))
        app.display.invert(has_t and not in_pos)
        app.display.show_measurement(pitch, target_str=target_str, ble=app.ble.enabled)
