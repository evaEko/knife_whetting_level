import time
from states.init import init
from states.measure import measure
from states.calibration import calibrate
from states.select_angle import select_angle
from states.power import off

time.sleep_ms(3000)


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
        elif event == ('long', 'low'):
            off()
        elif event == ('short', 'top'):
            select_angle()


main()
