import math
from horus.types import Pose, Derived, Metrics
from horus.perception.geometry import angle_3pt, back_angle


def compute_metrics(pose: Pose, derived: Derived) -> Metrics:
    knee_angle_left = angle_3pt(
        pose["left_hip"],
        pose["left_knee"],
        pose["left_ankle"],
    )

    knee_angle_right = angle_3pt(
        pose["right_hip"],
        pose["right_knee"],
        pose["right_ankle"],
    )

    hip_height = derived["hip_center"][1]

    stance_width = abs(pose["right_foot"][0] - pose["left_foot"][0])

    knee_track_left = pose["left_knee"][0] - pose["left_foot"][0]
    knee_track_right = pose["right_knee"][0] - pose["right_foot"][0]

    return {
        "knee_angle_left": knee_angle_left,
        "knee_angle_right": knee_angle_right,
        "hip_height": hip_height,
        "back_angle": back_angle(
            derived["hip_center"],
            derived["shoulder_center"],
        ),
        "stance_width": stance_width,
        "knee_track_left": knee_track_left,
        "knee_track_right": knee_track_right,
    }