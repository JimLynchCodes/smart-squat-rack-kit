from sensei.utils.pose_adapter import get_pose, joint, x


class ElbowStabilityFault:
    """
    Detects elbow instability:
    - inward collapse
    - forward/back jitter over time
    """

    name = "elbow_stability"

    def __init__(self):
        self.left_history = []
        self.right_history = []
        self.window = 8

        self._result = None

    # ---------------------------
    # MAIN LOGIC
    # ---------------------------
    def check(self, msg):

        pose = get_pose(msg)

        le = joint(pose, "left_elbow")
        re = joint(pose, "right_elbow")

        # ---------------------------
        # Safe exit
        # ---------------------------
        if not le or not re:
            self._result = None
            return self._result

        # track x-position (primary instability axis)
        self.left_history.append(x(le))
        self.right_history.append(x(re))

        # maintain rolling window
        if len(self.left_history) > self.window:
            self.left_history.pop(0)
            self.right_history.pop(0)

        # not enough data yet
        if len(self.left_history) < self.window:
            self._result = None
            return self._result

        # ---------------------------
        # instability computation
        # ---------------------------
        left_var = self._variance(self.left_history)
        right_var = self._variance(self.right_history)

        combined_var = left_var + right_var

        severity = min(1.0, combined_var / 0.02)  # tuned for normalized coords

        # ---------------------------
        # FAULT CONDITION
        # ---------------------------
        if severity > 0.15:
            self._result = {
                "fault": self.name,
                "severity": round(severity, 3),
                "metrics": {
                    "left_var": round(left_var, 6),
                    "right_var": round(right_var, 6),
                    "combined_var": round(combined_var, 6),
                }
            }
        else:
            self._result = None

        return self._result

    # ---------------------------
    # SENSEI CONTRACT
    # ---------------------------
    def result(self):
        return self._result

    # ---------------------------
    # UTILITY
    # ---------------------------
    def _variance(self, arr):
        mean = sum(arr) / len(arr)
        return sum((x - mean) ** 2 for x in arr) / len(arr)