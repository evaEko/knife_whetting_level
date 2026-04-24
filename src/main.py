from states.init import init
from states.measure import measure
from states.calibration import calibrate
from states.power import off


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


main()
