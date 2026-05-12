from core.container import Container
from helpers.setting_item import SettingItem
from core.app import App
from states.init_state import InitState
from states.flash_mode_state import FlashModeState

Container.init()

def _deviation():
    from states.settings.deviation_state import DeviationState
    return DeviationState()

def _surface():
    from states.settings.surface_level_state import SurfaceLevelState
    return SurfaceLevelState(
        storage_key='n_stone',
        prompt=("Level", "on stone", "top=esc", "low=capt"),
        saved_msg="Calibrated",
    )

def _target():
    from states.settings.surface_level_state import SurfaceLevelState
    return SurfaceLevelState(
        storage_key='n_target',
        prompt=("Blade", "at angle", "top=esc", "low=capt"),
        saved_msg="Target saved",
        on_save=Container.calibration_service.set_target,
    )

def _ble():
    from states.settings.ble_toggle_state import BleToggleState
    return BleToggleState()

def _exit():
    from states.measure_state import MeasureState
    return MeasureState()

def _clear_target():
    from states.settings.clear_target_state import ClearTargetState
    return ClearTargetState()

def _make_preset(angle):
    def _factory():
        from states.settings.set_preset_state import SetPresetState
        return SetPresetState(angle)
    return _factory

def build_angle_items():
    items = [SettingItem(name, _make_preset(angle), subtitle="{:g}".format(angle))
             for name, angle in Container.preset_store]
    items.append(SettingItem("Custom", _target))
    items.append(SettingItem("Clear",  _clear_target))
    items.append(SettingItem("Exit",   _exit))
    return items

Container.build_angle_items = build_angle_items

Container.settings_items = [
    SettingItem("Calibration", _surface),
    SettingItem("BLE",       _ble),
    SettingItem("Deviation", _deviation),
    SettingItem("Exit",      _exit),
]

app = App()
app.run(InitState(), global_events={
    'both': FlashModeState,
})