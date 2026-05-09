def get_pose(msg):
    """
    Normalizes Horus output into a stable interface.
    Prevents all schema-related crashes.
    """
    return msg.get("pose", {})


def joint(pose, name):
    """
    Safe joint accessor.
    Returns (x, y) or None.
    """
    val = pose.get(name)
    if val is None or len(val) != 2:
        return None
    return val


def x(p):
    return p[0] if p else None


def y(p):
    return p[1] if p else None