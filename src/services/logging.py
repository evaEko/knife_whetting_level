try:
    from utime import ticks_ms
except ImportError:
    from time import time as _time
    def ticks_ms():
        return int(_time() * 1000)


def log(message):
    print("[{t}] {msg}".format(t=ticks_ms(), msg=str(message)))
