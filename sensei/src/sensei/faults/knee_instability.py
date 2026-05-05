class KneeInstabilityFault:
    name = "knee_instability"

    def __init__(self):
        self.left_history = []
        self.right_history = []
        self.window = 8

    def check(self, msg, state):
        self.left_history.append(msg["left_knee_x"])
        self.right_history.append(msg["right_knee_x"])

        if len(self.left_history) > self.window:
            self.left_history.pop(0)
            self.right_history.pop(0)

        if len(self.left_history) < self.window:
            return 0.0

        left_var = self._variance(self.left_history)
        right_var = self._variance(self.right_history)

        severity = min(1.0, (left_var + right_var) / 200)

        return severity

    def _variance(self, arr):
        mean = sum(arr) / len(arr)
        return sum((x - mean) ** 2 for x in arr) / len(arr)

    def result(self, severity):
        return {
            "fault": self.name,
            "severity": severity
        }