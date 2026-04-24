import time
from states.init import init

time.sleep_ms(1000)
from states.measure import measure
from states.calibration import calibrate
from states.select_angle import select_angle
from states.flash import flash


def main():
    try:
        init()
    except Exception as e:
        print(f"INIT CRASH: {e}")
        return
    while True:
        event = measure()
        if event == ('short', 'low'):
            calibrate()
        elif event == ('short', 'top'):
            select_angle()
        elif event == ('long', 'top'):
            flash()


main()
