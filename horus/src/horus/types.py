from typing import TypedDict, List, Dict

class Point(TypedDict):
    x: float
    y: float

class PoseData(TypedDict):
    hip: List[float]
    knee: List[float]
    ankle: List[float]
    shoulder: List[float]

class DerivedData(TypedDict):
    knee_angle: float
    hip_angle: float
    vertical_velocity: float

# This matches the structure Sensei expects
class HorusPacket(TypedDict):
    frame_id: int
    pose: Dict[str, list]
    rep_phase: str
    metrics: Dict[str, float]
    bar: Dict[str, any]
    ts_cackle: float
    ts_horus: float
    