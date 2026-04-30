from horus.types import HorusResult
from horus.perception.pose import estimate_pose
from horus.perception.features import compute_metrics
from horus.perception.rep_state import RepStateMachine
from horus.perception.bar_path import BarPathTracker


class HorusPipeline:
    def __init__(self):
        self.rep = RepStateMachine()
        self.bar = BarPathTracker()

    def process(self, frame_id: int, front_frame, side_frame) -> HorusResult:
        pose = estimate_pose(front_frame, side_frame)

        metrics = compute_metrics(pose)
        rep_phase = self.rep.update(pose)

        # side-view proxy for bar position: shoulder tracks bar roughly
        bar_pos = pose["shoulder"]
        bar_dx = self.bar.update(bar_pos)

        return {
            "frame_id": frame_id,
            "pose": pose,
            "rep_phase": rep_phase,
            "metrics": metrics,
            "bar": {
                "position": bar_pos,
                "path_dx": bar_dx,
            },
        }