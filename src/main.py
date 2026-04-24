import time
import ctx
from states.init import init
from states.measure import measure
from states.calibration import calibrate
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
            if ctx.oled:
                import time
                ctx.oled.fill(0)
                ctx.oled.text("TOP BTN!", 16, 12, 1)
                ctx.oled.show()
                time.sleep_ms(2000)


main()
