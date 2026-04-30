from horus.types import Pose


def estimate_pose(front_frame, side_frame) -> Pose:
    """
    Placeholder pose extractor.
    Replace with MediaPipe / YOLO pose later.
    Coordinates normalized to [0,1].
    """

    return {
        "left_shoulder": (0.44, 0.34),
        "right_shoulder": (0.56, 0.34),

        "left_hip": (0.47, 0.58),
        "right_hip": (0.57, 0.58),

        "left_knee": (0.48, 0.78),
        "right_knee": (0.58, 0.78),

        "left_ankle": (0.47, 0.94),
        "right_ankle": (0.59, 0.94),

        "left_foot": (0.45, 0.98),
        "right_foot": (0.61, 0.98),
    }