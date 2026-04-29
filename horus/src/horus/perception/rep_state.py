class RepStateMachine:
    def __init__(self):
        self.prev = None

    def update(self, pose):
        hip_y = pose["hip"][1]

        if self.prev is None:
            self.prev = hip_y
            return "IDLE"

        delta = hip_y - self.prev

        if delta > 0.01:
            state = "DESCENT"
        elif delta < -0.01:
            state = "ASCENT"
        else:
            state = "BOTTOM"

        self.prev = hip_y
        return state