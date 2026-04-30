import math
from horus.types import Point, Pose, Derived


def midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def compute_derived(pose: Pose) -> Derived:
    shoulder_center = midpoint(pose["left_shoulder"], pose["right_shoulder"])
    hip_center = midpoint(pose["left_hip"], pose["right_hip"])

    # bar proxy: centered over shoulders
    bar_center = shoulder_center

    return {
        "shoulder_center": shoulder_center,
        "hip_center": hip_center,
        "bar_center": bar_center,
    }


def angle_3pt(a: Point, b: Point, c: Point) -> float:
    """
    Angle ABC in degrees.
    """
    ab = (a[0] - b[0], a[1] - b[1])
    cb = (c[0] - b[0], c[1] - b[1])

    dot = ab[0] * cb[0] + ab[1] * cb[1]
    mag_ab = math.hypot(ab[0], ab[1])
    mag_cb = math.hypot(cb[0], cb[1])

    if mag_ab == 0 or mag_cb == 0:
        return 0.0

    cos_theta = max(-1.0, min(1.0, dot / (mag_ab * mag_cb)))
    return math.degrees(math.acos(cos_theta))


def back_angle(hip_center: Point, shoulder_center: Point) -> float:
    dx = shoulder_center[0] - hip_center[0]
    dy = shoulder_center[1] - hip_center[1]

    angle = math.degrees(math.atan2(dx, -dy))
    return abs(angle)