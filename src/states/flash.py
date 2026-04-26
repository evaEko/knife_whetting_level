import sys
import ctx


def flash():
    if ctx.oled:
        ctx.oled.invert(False)
        ctx.oled.fill(0)
        ctx.oled.text("Ready to", 4, 8, 1)
        ctx.oled.text("flash...", 16, 20, 1)
        ctx.oled.show()
    print("-> REPL")
    sys.exit()
