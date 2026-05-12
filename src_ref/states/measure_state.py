from core.state import State
from core.container import Container


class MeasureState(State):
    def __init__(self):
        self._target_str = None

    def enter(self):
        Container.calibration_service.load()
        if not Container.calibration_service.has_stone():
            Container.display_service.show_text("No surface", "calibration", "Go to Settings")
            Container.logging_service.log("[MeasureState] no n_stone in storage")
            return
        target = Container.calibration_service.target_angle()
        self._target_str = "{:.1f}".format(target) if target is not None else None
        Container.display_service.show_text("Measuring...")
        Container.logging_service.log("[MeasureState] enter")

    def update(self):
        if Container.button_event == 'short_top':
            from states.angle_select_state import AngleSelectState
            return AngleSelectState(Container.build_angle_items())
        if Container.button_event == 'short_low':
            from states.settings_state import SettingsState
            return SettingsState(Container.settings_items)

        if Container.calibration_service.has_stone():
            Container.measure_service.update()
            pitch = Container.measure_service.pitch()
            Container.display_service.invert(
                Container.calibration_service.has_target() and not Container.measure_service.in_position()
            )
            Container.display_service.show_measurement(
                pitch,
                target_str=self._target_str,
                ble=Container.ble_service.enabled,
            )

        return None

    def exit(self):
        Container.display_service.invert(False)
        Container.logging_service.log("[MeasureState] exit")

