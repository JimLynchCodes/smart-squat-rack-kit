import numpy as np
import time
from ultralytics import YOLO


class SquatPipeline:
    """
    Horus Vision Pipeline (stable v2)

    Input:
        - side_img (numpy BGR frame from OpenCV)

    Output:
        - pose dict
        - rep_phase
        - instant_metrics
        - bar dynamics
    """

    def __init__(self):

        # ---------------------------
        # YOLO MODEL
        # ---------------------------
        self.model = YOLO("yolov8n-pose.pt")

        # ---------------------------
        # MOTION STATE
        # ---------------------------
        self.prev_bar_y = None
        self.prev_ts = None
        self.prev_velocity = 0.0

        # smoothing (stability boost)
        self.alpha = 0.25
        self.smooth_vel = 0.0
        self.smooth_accel = 0.0

    # =========================================================
    # UTIL
    # =========================================================
    def midpoint(self, p1, p2):
        return [
            (p1[0] + p2[0]) * 0.5,
            (p1[1] + p2[1]) * 0.5,
        ]

    # =========================================================
    # MAIN PIPELINE
    # =========================================================
    def process(self, front_img, side_img):

        # ---------------------------
        # SAFETY CHECK (IMPORTANT)
        # ---------------------------
        if side_img is None:
            return {}, "NO_PERSON", {}, {}

        # YOLO inference
        results = self.model(side_img, verbose=False)[0]

        if results.keypoints is None or len(results.keypoints.data) == 0:
            return {}, "NO_PERSON", {}, {}

        kp = results.keypoints.xyn[0].cpu().numpy()

        def get(i):
            if i >= len(kp):
                return [0.0, 0.0]
            return kp[i].tolist()

        # ---------------------------
        # KEYPOINTS
        # ---------------------------
        l_hip, r_hip = get(11), get(12)
        l_knee, r_knee = get(13), get(14)
        l_ankle, r_ankle = get(15), get(16)
        l_sh, r_sh = get(5), get(6)

        hip_mid = self.midpoint(l_hip, r_hip)
        knee_mid = self.midpoint(l_knee, r_knee)
        ankle_mid = self.midpoint(l_ankle, r_ankle)
        sh_mid = self.midpoint(l_sh, r_sh)

        # ---------------------------
        # ANGLES
        # ---------------------------

        # knee angle
        ba = np.array(l_hip) - np.array(l_knee)
        bc = np.array(l_ankle) - np.array(l_knee)

        knee_cos = np.dot(ba, bc) / (
            np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6
        )

        knee_angle = np.degrees(
            np.arccos(np.clip(knee_cos, -1.0, 1.0))
        )

        # back angle
        back_vec = np.array(sh_mid) - np.array(hip_mid)

        back_angle = np.degrees(
            np.arctan2(abs(back_vec[0]), abs(back_vec[1]) + 1e-6)
        )

        # ---------------------------
        # BAR TRACKING
        # ---------------------------
        now = time.time()
        bar_y = sh_mid[1]

        vel_y = 0.0
        accel_y = 0.0

        if self.prev_ts is not None and self.prev_bar_y is not None:

            dt = now - self.prev_ts

            if 0 < dt < 0.5:

                raw_vel = (bar_y - self.prev_bar_y) / dt

                # smoothing
                self.smooth_vel = (
                    self.alpha * raw_vel
                    + (1 - self.alpha) * self.smooth_vel
                )

                vel_y = self.smooth_vel

                raw_accel = (vel_y - self.prev_velocity) / dt

                self.smooth_accel = (
                    self.alpha * raw_accel
                    + (1 - self.alpha) * self.smooth_accel
                )

                accel_y = self.smooth_accel

        self.prev_bar_y = bar_y
        self.prev_ts = now
        self.prev_velocity = vel_y

        # ---------------------------
        # PHASE DETECTION
        # ---------------------------
        THRESH = 0.01

        if abs(vel_y) < THRESH:
            phase = "LOCKOUT"
        elif vel_y > THRESH:
            phase = "DESCENT"
        else:
            phase = "ASCENT"

        # ---------------------------
        # OUTPUT METRICS
        # ---------------------------
        pose = {
            "left_hip": l_hip,
            "right_hip": r_hip,
            "hips_midpoint": hip_mid,

            "left_knee": l_knee,
            "right_knee": r_knee,
            "knees_midpoint": knee_mid,

            "left_ankle": l_ankle,
            "right_ankle": r_ankle,
            "ankles_midpoint": ankle_mid,

            "left_shoulder": l_sh,
            "right_shoulder": r_sh,
            "shoulders_midpoint": sh_mid,

            "score": float(results.boxes.conf[0]) if results.boxes is not None else 0.9,
            "direction": "LEFT" if l_sh[0] < r_sh[0] else "RIGHT",
        }

        metrics = {
            "back_angle": round(back_angle, 2),
            "knee_angle_proxy": round(knee_angle, 2),
            "knee_dist": abs(l_knee[0] - r_knee[0]),
            "hip_y": round(hip_mid[1], 4),
            "depth_relative_to_knee": round(
                knee_mid[1] - hip_mid[1], 4
            ),
        }

        bar = {
            "position": bar_y,
            "velocity_y": round(vel_y, 4),
            "acceleration_y": round(accel_y, 4),
        }

        return pose, phase, metrics, bar