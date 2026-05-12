import math


def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def pitch(g, n_stone):
    """0 = flat on stone, positive = blade lifted. Values > 90° are folded back."""
    dot = _clamp(_dot(g, n_stone), -1.0, 1.0)
    raw = math.acos(dot) * 180.0 / math.pi
    return 180.0 - raw if raw > 90.0 else raw
