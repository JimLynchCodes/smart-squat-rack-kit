from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FrameSync:
    frame_id: int
    front_ok: bool
    side_ok: bool


@dataclass
class PoseOutput:
    frame_id: int
    keypoints: Dict[str, Any]


@dataclass
class MotionState:
    frame_id: int
    phase: str  # DESCENT | BOTTOM | ASCENT | LOCKOUT
    metrics: Dict[str, float]