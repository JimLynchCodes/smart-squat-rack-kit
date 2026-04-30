from dataclasses import dataclass, asdict




@dataclass
class FramePacket:
   camera: str
   frame_id: int
   ts_monotonic: float
   ts_wall: float
   width: int
   height: int
   ok: bool


   def to_dict(self) -> dict:
       return asdict(self)
