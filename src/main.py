from states.init import init
from states.measure import measure
from states.calibration import calibrate
from states.power import off


def main():
    init()
    while True:
        event = measure()
        if event == 'short':
            calibrate()
        elif event == 'long':
            off()


main()
