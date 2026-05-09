from sensei.utils.pose_adapter import get_pose, joint, x


class WeightDistributionFault:
    """
    Detects left/right weight imbalance by comparing
    hip center vs foot base center.
    """

    name = "weight_distribution"

    def __init__(self):
        self._result = None

    # ---------------------------
    # MAIN LOGIC
    # ---------------------------
    def check(self, msg):

        pose = get_pose(msg)

        hip = joint(pose, "hips_midpoint")
        l_ankle = joint(pose, "left_ankle")
        r_ankle = joint(pose, "right_ankle")

        # ---------------------------
        # Safe exit
        # ---------------------------
        if not hip or not l_ankle or not r_ankle:
            self._result = None
            return self._result

        hip_x = x(hip)
        left_ankle_x = x(l_ankle)
        right_ankle_x = x(r_ankle)

        # base of support center
        center_base = (left_ankle_x + right_ankle_x) / 2

        offset = abs(hip_x - center_base)

        # ---------------------------
        # normalize severity (tuned for 0–1 space)
        # ---------------------------
        severity = min(1.0, offset / 0.25)  # tuned for normalized coords

        if severity > 0.15:
            self._result = {
                "fault": self.name,
                "severity": round(severity, 3),
                "metrics": {
                    "hip_x": round(hip_x, 4),
                    "center_base": round(center_base, 4),
                    "offset": round(offset, 4),
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