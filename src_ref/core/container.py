from services.battery import BatteryService
from services.ble import BleService
from services.buttons import ButtonService
from services.calibration import CalibrationService
from services.config import ConfigService
from services.display import DisplayService
from services.imu import ImuService
from services.logging import LoggingService
from services.measure import MeasureService
from services.preset_store import PresetStore
from services.storage import StorageService


class Container:
    battery_service      = None
    ble_service          = None
    button_event         = None
    button_service       = None
    calibration_service  = None
    config_service       = ConfigService
    display_service      = None
    imu_service          = None
    logging_service      = LoggingService
    measure_service      = None
    preset_store         = None
    settings_items       = None
    angle_items          = None
    storage_service      = None

    @classmethod
    def init(cls):
        cls.config_service.load("config.txt")

        cls.storage_service = StorageService("data.txt")
        cls.storage_service.load()
        cls.display_service = DisplayService(
            sda_pin=cls.config_service.sda_oled,
            scl_pin=cls.config_service.sck_oled,
            i2c_id=cls.config_service.i2c_id_oled,
            addr=cls.config_service.oled_addr,
        )
        cls.button_service = ButtonService(
            pin_low=cls.config_service.btn_low,
            pin_top=cls.config_service.btn_top,
        )
        cls.imu_service = ImuService(
            sda_pin=cls.config_service.sda_imu,
            scl_pin=cls.config_service.scl_imu,
            i2c_id=cls.config_service.i2c_id_imu,
            addr=cls.config_service.bno085_addr,
        )
        cls.calibration_service = CalibrationService(
            storage=cls.storage_service,
        )
        cls.measure_service = MeasureService(
            imu_service=cls.imu_service,
            calibration_service=cls.calibration_service,
            config_service=cls.config_service,
            logging_service=cls.logging_service,
        )
        cls.ble_service     = BleService()
        cls.battery_service = BatteryService(
            display_service=cls.display_service,
            button_service=cls.button_service,
        )
        cls.preset_store    = PresetStore()
        cls.preset_store.load()
