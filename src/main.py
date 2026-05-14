from services.battery import BatteryService
from services.ble import BleService
from services.ble_handler import BleCommandHandler
from services.buttons import ButtonService
from services.calibration import CalibrationService
from services.config import ConfigService
from services.display import DisplayService
from services.imu import ImuService
from services.logging import LoggingService
from services.measure import MeasureService
from services.preset_store import PresetStore
from services.storage import StorageService
from helpers.setting_item import SettingItem
from core.app import App
from states.init_state import InitState
from states.flash_mode_state import FlashModeState

config      = ConfigService("config.txt")
logging     = LoggingService()

storage     = StorageService("data.txt")
storage.load()
display     = DisplayService(
    sda_pin=config.sda_oled,
    scl_pin=config.sck_oled,
    i2c_id=config.i2c_id_oled,
    addr=config.oled_addr,
)
buttons     = ButtonService(
    pin_low=config.btn_low,
    pin_top=config.btn_top,
)
imu         = ImuService(
    sda_pin=config.sda_imu,
    scl_pin=config.scl_imu,
    i2c_id=config.i2c_id_imu,
    addr=config.bno085_addr,
)
calibration = CalibrationService(storage=storage)
measure     = MeasureService(
    imu_service=imu,
    calibration_service=calibration,
    config_service=config,
    logging_service=logging,
)
presets     = PresetStore()
presets.load()
ble         = BleService()
ble_handler = BleCommandHandler(
    ble_service=ble,
    calibration_service=calibration,
    measure_service=measure,
    preset_store=presets,
    config_service=config,
    imu_service=imu,
)
battery     = BatteryService(
    display_service=display,
    button_service=buttons,
)


def _deviation():
    from states.settings_handlers.deviation_handler import DeviationHandler
    return DeviationHandler()

def _surface():
    from states.settings_handlers.surface_level_handler import SurfaceLevelHandler
    return SurfaceLevelHandler(
        storage_key='n_stone',
        prompt=("Level", "on stone", "top=esc", "low=capt"),
        saved_msg="Calibrated",
        on_save=calibration.set_stone,
    )

def _target():
    from states.settings_handlers.surface_level_handler import SurfaceLevelHandler
    return SurfaceLevelHandler(
        storage_key='n_target',
        prompt=("Blade", "at angle", "top=esc", "low=capt"),
        saved_msg="Target saved",
        on_save=calibration.set_target,
    )

def _ble():
    from states.settings_handlers.ble_toggle_handler import BleToggleHandler
    return BleToggleHandler()

def _exit(app):
    return 'measure'

def _clear_target(app):
    import time
    app.calibration.clear_target()
    app.display.show_splash("Cleared")
    time.sleep_ms(1500)
    return 'measure'

def _make_preset(angle):
    def action(app):
        import time
        app.calibration.set_target_angle(angle)
        app.display.show_splash("{:.1f}".format(angle))
        time.sleep_ms(1500)
        return 'measure'
    return action

def build_angle_items():
    items = [SettingItem(name, action=_make_preset(angle), subtitle="{:g}".format(angle))
             for name, angle in presets]
    items.append(SettingItem("Custom", handler=_target))
    items.append(SettingItem("Clear",  action=_clear_target))
    items.append(SettingItem("Exit",   action=_exit))
    return items


app = App(
    display=display,
    logging=logging,
    imu=imu,
    buttons=buttons,
    storage=storage,
    config=config,
    calibration=calibration,
    measure=measure,
    ble=ble,
    ble_handler=ble_handler,
    battery=battery,
    presets=presets,
    settings_items=[
        SettingItem("Calibration", handler=_surface),
        SettingItem("BLE",         handler=_ble),
        SettingItem("Deviation",   handler=_deviation),
        SettingItem("Exit",        action=_exit),
    ],
    build_angle_items=build_angle_items,
)

if config.ble_enabled:
    ble.toggle()

app.run(InitState(), global_events={
    'both': FlashModeState,
})
