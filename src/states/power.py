import machine
import time
import ctx
from machine import Pin


def off():
    print("-> POWER OFF")
    ctx.oled.fill(0)
    ctx.oled.text("OFF", 24, 16, 1)
    ctx.oled.show()
    time.sleep_ms(500)
    ctx.oled.fill(0)
    ctx.oled.show()
    ctx.oled._cmd(0xAE)
    ctx.imu.suspend()

    wake_pending = [False]
    def on_btn_press(pin):
        wake_pending[0] = True

    ctx.btn.pin.irq(trigger=Pin.IRQ_FALLING, handler=on_btn_press)
    while True:
        machine.idle()
        if wake_pending[0] or ctx.btn.is_pressed():
            wake_pending[0] = False
            start = time.ticks_ms()
            while ctx.btn.is_pressed():
                time.sleep_ms(10)
            if time.ticks_diff(time.ticks_ms(), start) >= 30:
                ctx.btn.pin.irq(handler=None)
                print("-> WAKE UP")
                machine.reset()
