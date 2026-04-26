import sys
import ctx


def flash():
    if ctx.oled:
        ctx.oled.invert(False)
        ctx.oled.fill(0)
        ctx.oled.text("Flash mode", 4, 8, 1)
        ctx.oled.text("ready...", 16, 20, 1)
        ctx.oled.show()
    print("-> REPL")
    sys.exit()
