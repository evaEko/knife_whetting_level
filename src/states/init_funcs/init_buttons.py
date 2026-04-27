import ctx
from drivers.button import Button
from config import BTN_LOW, BTN_TOP


def init_buttons():
    try:
        ctx.btn_low = Button(BTN_LOW)
        ctx.btn_top = Button(BTN_TOP)
        print("BTN OK")
    except Exception as e:
        print(f"BTN ERROR: {e}")
