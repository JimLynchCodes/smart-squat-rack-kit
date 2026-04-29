from horus.perception.pose import estimate_pose
from horus.perception.rep_state import RepStateMachine
from horus.perception.features import compute_metrics


class HorusPipeline:
    def __init__(self):
        self.rep = RepStateMachine()

    def process(self, frame_id, frame):
        pose = estimate_pose(frame)
        state = self.rep.update(pose)
        metrics = compute_metrics(pose)

        return {
            "frame_id": frame_id,
            "phase": state,
            "metrics": metrics
        }