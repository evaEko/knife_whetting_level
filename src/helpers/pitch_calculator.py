import math


def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _cross_norm(a, b):
    cx = a[1]*b[2] - a[2]*b[1]
    cy = a[2]*b[0] - a[0]*b[2]
    cz = a[0]*b[1] - a[1]*b[0]
    return math.sqrt(cx*cx + cy*cy + cz*cz)


def pitch(g, n_stone):
    """0 = flat on stone, positive = blade lifted. Values > 90° are folded back."""
    raw = math.degrees(math.atan2(_cross_norm(g, n_stone), _dot(g, n_stone)))
    return 180.0 - raw if raw > 90.0 else raw
