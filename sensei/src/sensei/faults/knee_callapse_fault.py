from sensei.utils.pose_adapter import get_pose, joint, x, y
from sensei.faults.base import BaseFault


class KneeCollapseFault(BaseFault):

    def check(self, msg):

        pose = get_pose(msg)

        lk = joint(pose, "left_knee")
        rk = joint(pose, "right_knee")
        lh = joint(pose, "left_hip")
        rh = joint(pose, "right_hip")

        # ---------------------------
        # Safe exit
        # ---------------------------
        if not lk or not rk or not lh or not rh:
            self._result = None
            return self._result

        knee_center_x = (x(lk) + x(rk)) / 2
        hip_center_x = (x(lh) + x(rh)) / 2

        knee_offset = abs(knee_center_x - hip_center_x)

        # ---------------------------
        # FAULT LOGIC
        # ---------------------------
        if knee_offset < 0.03:
            self._result = {
                "fault": "KNEE_COLLAPSE",
                "severity": "high",
                "value": round(knee_offset, 4),
            }
        else:
            self._result = None

        return self._result