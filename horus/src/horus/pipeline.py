import numpy as np
import time
from ultralytics import YOLO
from horus.utils import to_float


class SquatPipeline:

    def __init__(self):

        self.model = YOLO("yolov8n-pose.pt")
        self.model.overrides["verbose"] = False

        self.prev_bar_y = None
        self.prev_ts = None

    # -------------------------
    def midpoint(self, a, b):
        return [(a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5]

    def angle(self, v1, v2):
        v1 = np.array(v1, dtype=np.float32)
        v2 = np.array(v2, dtype=np.float32)

        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)

        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0

        cos = np.dot(v1, v2) / (n1 * n2)
        return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))

    # -------------------------
    def process(self, front_img, side_img):

        if side_img is None:
            return {}, "NO_PERSON", {}, {}

        side = self.model(side_img, verbose=False)[0]
        front = self.model(front_img, verbose=False)[0] if front_img is not None else None

        if side.keypoints is None or len(side.keypoints.data) == 0:
            return {}, "NO_PERSON", {}, {}

        skp = side.keypoints.xyn[0].cpu().numpy()
        fkp = front.keypoints.xyn[0].cpu().numpy() if front else skp

        def g(kp, i):
            if i >= len(kp):
                return [0.0, 0.0]
            return kp[i].tolist()

        # SIDE
        l_sh, r_sh = g(skp, 5), g(skp, 6)
        l_el, r_el = g(skp, 7), g(skp, 8)
        l_wr, r_wr = g(skp, 9), g(skp, 10)

        l_hip, r_hip = g(skp, 11), g(skp, 12)
        l_knee, r_knee = g(skp, 13), g(skp, 14)
        l_ankle, r_ankle = g(skp, 15), g(skp, 16)

        hip_mid = self.midpoint(l_hip, r_hip)
        sh_mid = self.midpoint(l_sh, r_sh)

        # FRONT
        fl_knee, fr_knee = g(fkp, 13), g(fkp, 14)
        fl_ankle, fr_ankle = g(fkp, 15), g(fkp, 16)

        # -------------------------
        # METRICS
        # -------------------------
        back_angle = self.angle(np.array(sh_mid) - np.array(hip_mid), [0, -1])

        knee_angle = self.angle(
            np.array(l_hip) - np.array(l_knee),
            np.array(l_ankle) - np.array(l_knee),
        )

        forearm_angle = 0.5 * (
            self.angle(np.array(l_wr) - np.array(l_el), [0, -1]) +
            self.angle(np.array(r_wr) - np.array(r_el), [0, -1])
        )

        knee_valgus = abs(fl_knee[0] - fr_knee[0]) if front_img is not None else 0.0

        # -------------------------
        # BAR
        # -------------------------
        now = time.time()
        bar_y = sh_mid[1]

        vel_y = 0.0

        if self.prev_ts:
            dt = now - self.prev_ts
            if dt > 0:
                vel_y = (bar_y - self.prev_bar_y) / dt

        self.prev_ts = now
        self.prev_bar_y = bar_y

        # -------------------------
        # OUTPUT
        # -------------------------
        pose = {
            "side": {
                "left_hip": l_hip,
                "right_hip": r_hip,
                "left_knee": l_knee,
                "right_knee": r_knee,
                "left_ankle": l_ankle,
                "right_ankle": r_ankle,
            },
            "front": {
                "left_knee": fl_knee,
                "right_knee": fr_knee,
                "left_ankle": fl_ankle,
                "right_ankle": fr_ankle,
            }
        }

        metrics = {
            "side": {
                "back_angle": to_float(round(back_angle, 2)),
                "knee_angle": to_float(round(knee_angle, 2)),
                "forearm_angle": to_float(round(forearm_angle, 2)),
            },
            "front": {
                "knee_valgus": to_float(knee_valgus),
            }
        }

        bar = {
            "velocity_y": to_float(vel_y),
            "position": to_float(bar_y),
        }

        return pose, "UNKNOWN", metrics, bar