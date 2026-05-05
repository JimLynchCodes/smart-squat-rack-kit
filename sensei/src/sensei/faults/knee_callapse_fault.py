class KneeCollapseFault:
    def __init__(self):
        self.triggered = False

    def check(self, msg):
        left_knee = msg["left_knee_x"]
        left_foot = msg["left_foot_x"]

        # simple heuristic: knee too far inward
        if left_knee < left_foot:
            self.triggered = True

    def result(self):
        return {
            "fault": "knee_collapse",
            "triggered": self.triggered
        }