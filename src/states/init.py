import sys
sys.path.insert(0, 'states/init_funcs')

from init_oled import init_oled
from init_buttons import init_buttons
from check_battery import check_battery
from init_sensor import init_sensor
from load_preset_angles import load_preset_angles
from set_board_level import set_board_level
from load_recent_angle import load_recent_angle

sys.path.pop(0)


def init():
    init_oled()
    init_buttons()
    check_battery()
    init_sensor()
    load_preset_angles()
    set_board_level()
    load_recent_angle()
