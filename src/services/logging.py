from utime import ticks_ms


class LoggingService:
    @staticmethod
    def log(message):
        print("[{t}] {msg}".format(t=ticks_ms(), msg=str(message)))
