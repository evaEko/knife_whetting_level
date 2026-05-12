from core.state import State
from core.container import Container


class MeasureState(State):
    def __init__(self):
        pass

    def enter(self):
        Container.calibration_service.load()
        if not Container.calibration_service.has_stone():
            Container.display_service.show_text("No surface", "calibration", "Go to Settings")
            Container.logging_service.log("[MeasureState] no n_stone in storage")
            return
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

        Container.ble_handler.tick()

        if Container.calibration_service.has_stone():
            pitch = Container.measure_service.pitch()
            has_t = Container.calibration_service.has_target()
            in_pos = Container.measure_service.in_position()
            target = Container.calibration_service.target_angle()
            target_str = "{:.1f}".format(target) if target is not None else None
            Container.logging_service.log("pitch={:.2f} target={} has_target={} in_pos={}".format(
                pitch, target, has_t, in_pos))
            Container.display_service.invert(has_t and not in_pos)
            Container.display_service.show_measurement(
                pitch,
                target_str=target_str,
                ble=Container.ble_service.enabled,
            )

        return None

    def exit(self):
        Container.display_service.invert(False)
        Container.logging_service.log("[MeasureState] exit")

