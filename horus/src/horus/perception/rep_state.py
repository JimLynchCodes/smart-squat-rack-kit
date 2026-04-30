from horus.types import Derived, RepPhase


class RepStateMachine:
    def __init__(self):
        self.prev_hip_y: float | None = None
        self.phase: RepPhase = "IDLE"

    def update(self, derived: Derived) -> RepPhase:
        hip_y = derived["hip_center"][1]

        if self.prev_hip_y is None:
            self.prev_hip_y = hip_y
            self.phase = "IDLE"
            return self.phase

        delta = hip_y - self.prev_hip_y

        if delta > 0.01:
            self.phase = "DESCENT"
        elif delta < -0.01:
            self.phase = "ASCENT"
        else:
            self.phase = "BOTTOM"

        self.prev_hip_y = hip_y
        return self.phase