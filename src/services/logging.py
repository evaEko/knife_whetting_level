from utime import ticks_ms


class LoggingService:
    def log(self, message):
        print("[{t}] {msg}".format(t=ticks_ms(), msg=str(message)))
