import ctx
from config import ANGLE_FORMAT, LOAD_TARGET_ANGLE_FROM_EEPROM


def load_recent_angle():
    ctx.load_settings(load_target_angle=LOAD_TARGET_ANGLE_FROM_EEPROM)
    ctx.angle_format = ctx.get_angle_format(ANGLE_FORMAT)
