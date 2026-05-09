import numpy as np


def to_float(x):
    try:
        return float(x)
    except Exception:
        try:
            return float(np.array(x))
        except Exception:
            return 0.0


def safe_list(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, list):
        return x
    try:
        return list(x)
    except Exception:
        return []


def json_safe(obj):
    """
    Recursively sanitize Horus output for ZMQ JSON.
    """

    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if hasattr(obj, "item"):
        return obj.item()

    return obj