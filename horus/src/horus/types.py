from typing import Literal, TypedDict


Point = tuple[float, float]
RepPhase = Literal["IDLE", "DESCENT", "BOTTOM", "ASCENT"]


class Pose(TypedDict):
    left_shoulder: Point
    right_shoulder: Point

    left_hip: Point
    right_hip: Point

    left_knee: Point
    right_knee: Point

    left_ankle: Point
    right_ankle: Point

    left_foot: Point
    right_foot: Point


class Derived(TypedDict):
    shoulder_center: Point
    hip_center: Point
    bar_center: Point


class Metrics(TypedDict):
    knee_angle_left: float
    knee_angle_right: float
    hip_height: float
    back_angle: float
    stance_width: float
    knee_track_left: float
    knee_track_right: float


class Bar(TypedDict):
    position: Point
    path_dx: float


class HorusResult(TypedDict):
    frame_id: int
    pose: Pose
    derived: Derived
    rep_phase: RepPhase
    metrics: Metrics
    bar: Bar