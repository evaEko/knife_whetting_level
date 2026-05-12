import math


def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


class PitchCalculator:
    @staticmethod
    def pitch(g, n_stone):
        """Return sharpening angle in degrees. 0 = flat on stone, positive = blade lifted.
        Raw values > 90 are folded: 180->0, 179->1, ..., 91->89.
        Raw values 0-90 are returned unchanged."""
        dot = _clamp(_dot(g, n_stone), -1.0, 1.0)
        raw = math.acos(dot) * 180.0 / math.pi
        return 180.0 - raw if raw > 90.0 else raw
