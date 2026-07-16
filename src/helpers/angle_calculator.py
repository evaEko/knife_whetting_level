import math


def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _cross_norm(a, b):
    cx = a[1]*b[2] - a[2]*b[1]
    cy = a[2]*b[0] - a[0]*b[2]
    cz = a[0]*b[1] - a[1]*b[0]
    return math.sqrt(cx*cx + cy*cy + cz*cz)


def quaternion_to_gravity(quat):
    """Gravity unit vector (gx, gy, gz) in the sensor frame from a (w, x, y, z) quaternion."""
    w, x, y, z = quat
    return (
        2.0 * (w * y - x * z),
        -2.0 * (y * z + x * w),
        2.0 * (x * x + y * y) - 1.0,
    )


def angle_between(a, b):
    """Unsigned angle in degrees between two vectors (0..180)."""
    return math.degrees(math.atan2(_cross_norm(a, b), _dot(a, b)))


def calculate_angle(gravity, surface_normal):
    """Blade angle above the stone: 0 = flat, positive = lifted. Values > 90° are folded back."""
    raw = angle_between(gravity, surface_normal)
    return 180.0 - raw if raw > 90.0 else raw
