# What it detects
# elbows collapsing inward
# elbows drifting too far forward/back unpredictably

class ElbowStabilityFault:
    name = "elbow_stability"

    def __init__(self):
        self.history = []
        self.window = 8

    def check(self, msg, state):
        if "left_elbow_x" not in msg:
            return 0.0

        self.history.append(msg["left_elbow_x"])

        if len(self.history) > self.window:
            self.history.pop(0)

        if len(self.history) < self.window:
            return 0.0

        var = self._variance(self.history)

        severity = min(1.0, var / 150)

        return severity

    def _variance(self, arr):
        mean = sum(arr) / len(arr)
        return sum((x - mean) ** 2 for x in arr) / len(arr)

    def result(self, severity):
        return {
            "fault": self.name,
            "severity": severity
        }