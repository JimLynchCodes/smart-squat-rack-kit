from sensei.utils.pose_adapter import get_pose, joint, x


class KneeInstabilityFault:
    """
    Detects knee wobble / instability based on lateral variance
    over a sliding window.
    """

    name = "knee_instability"

    def __init__(self):
        self.left_history = []
        self.right_history = []
        self.window = 8

        self._result = None

    # ---------------------------
    # MAIN UPDATE FUNCTION
    # ---------------------------
    def check(self, msg):

        pose = get_pose(msg)

        lk = joint(pose, "left_knee")
        rk = joint(pose, "right_knee")

        # ---------------------------
        # Safe guard
        # ---------------------------
        if not lk or not rk:
            self._result = None
            return self._result

        self.left_history.append(x(lk))
        self.right_history.append(x(rk))

        # keep sliding window
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

        severity = min(1.0, (left_var + right_var) / 200)

        if severity > 0.2:
            self._result = {
                "fault": self.name,
                "severity": round(severity, 3),
                "metrics": {
                    "left_var": round(left_var, 4),
                    "right_var": round(right_var, 4),
                }
            }
        else:
            self._result = None

        return self._result

    # ---------------------------
    # RESULT ACCESSOR (Sensei contract)
    # ---------------------------
    def result(self):
        return self._result

    # ---------------------------
    # UTILITY
    # ---------------------------
    def _variance(self, arr):
        mean = sum(arr) / len(arr)
        return sum((x - mean) ** 2 for x in arr) / len(arr)