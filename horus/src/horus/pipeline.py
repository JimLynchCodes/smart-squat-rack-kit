import numpy as np
from ultralytics import YOLO
from horus.utils import to_float


class SquatPipeline:
    def __init__(self):
        self.model = YOLO("yolov8n-pose.pt")
        self.model.overrides["verbose"] = False

        self.prev_bar_y = None
        self.prev_ts = None

        # Rep State Tracking
        self.standing_y = None
        self.is_repping = False
        self.rep_threshold = 0.05

        self.reset_rep_metrics()

    def midpoint(self, a, b):
        return [(a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5]

    def dist_x(self, a, b):
        return abs(a[0] - b[0])

    def is_valid(self, *pts):
        for pt in pts:
            if pt is None or (pt[0] == 0.0 and pt[1] == 0.0):
                return False
        return True

    def angle(self, v1, v2):
        v1 = np.array(v1, dtype=np.float32)
        v2 = np.array(v2, dtype=np.float32)

        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)

        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0

        cos = np.dot(v1, v2) / (n1 * n2)
        return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))

    def extract_keypoints(self, results, threshold=0.5):
        if results.keypoints is None or len(results.keypoints.data) == 0:
            return {}

        kp = results.keypoints.xyn[0].cpu().numpy()
        conf = results.keypoints.conf[0].cpu().numpy()

        # UPDATED: Added eyes and ears mapping
        mapping = {
            "nose": 0,
            "left_eye": 1,
            "right_eye": 2,
            "left_ear": 3,
            "right_ear": 4,

            "left_shoulder": 5,
            "right_shoulder": 6,

            "left_elbow": 7,
            "right_elbow": 8,

            "left_wrist": 9,
            "right_wrist": 10,

            "left_hip": 11,
            "right_hip": 12,

            "left_knee": 13,
            "right_knee": 14,

            "left_ankle": 15,
            "right_ankle": 16
        }

        res = {}

        for name, idx in mapping.items():
            if idx < len(kp) and conf[idx] > threshold:
                res[name] = kp[idx].tolist()
            else:
                res[name] = [0.0, 0.0]

        return res

    def get_side_elbow_flare(self, pts):
        candidates = []
        shoulder_width = 0.0

        if self.is_valid(pts.get("left_shoulder"), pts.get("right_shoulder")):
            shoulder_width = self.dist_x(pts["left_shoulder"], pts["right_shoulder"])

        shoulder_width = max(0.01, shoulder_width)

        if self.is_valid(pts.get("left_shoulder"), pts.get("left_elbow")):
            flare = (pts["left_elbow"][0] - pts["left_shoulder"][0]) / shoulder_width
            candidates.append(flare)

        if self.is_valid(pts.get("right_shoulder"), pts.get("right_elbow")):
            flare = (pts["right_elbow"][0] - pts["right_shoulder"][0]) / shoulder_width
            candidates.append(flare)

        if not candidates:
            return 0.0

        return float(sum(candidates) / len(candidates))

    def reset_rep_metrics(self):
        # Back Angle
        self.back_min = float('inf')
        self.back_max = float('-inf')
        self.back_sum = 0.0
        self.back_count = 0

        # Depth
        self.max_hip_knee_ratio = -1.0

        # Forward Drift
        self.max_fwd_drift = float('-inf')
        self.min_fwd_drift = float('inf')

        # Knee Distance
        self.knee_dist_min = float('inf')
        self.knee_dist_max = float('-inf')
        self.knee_dist_sum = 0.0
        self.knee_dist_count = 0

        # Elbow Flare
        self.max_elbow_flare = float("-inf")
        self.min_elbow_flare = float("inf")

        # Frame Trackers
        self.id_max_angle = None
        self.id_min_angle = None
        self.id_lowest_depth = None
        self.id_max_fwd_drift = None
        self.id_min_fwd_drift = None
        self.id_max_knee_dist = None
        self.id_min_knee_dist = None
        self.id_max_elbow_flare = None
        self.id_min_elbow_flare = None

    def process(self, front_img, side_img, frame_id=None):
        side_res = self.model(side_img, verbose=False)[0] if side_img is not None else None
        front_res = self.model(front_img, verbose=False)[0] if front_img is not None else None

        side_pts = self.extract_keypoints(side_res) if side_res else {}
        front_pts = self.extract_keypoints(front_res) if front_res else {}

        if not side_pts and not front_pts:
            return {}, "NO_PERSON", {}, {}, None

        metrics = {"side": {}, "front": {}}
        rep_summary = None

        # ---------------------------
        # SIDE VIEW
        # ---------------------------
        sh_mid = [0.0, 0.0]
        hip_mid = [0.0, 0.0]
        knee_mid = [0.0, 0.0]
        ankle_mid = [0.0, 0.0]

        cur_angle = 0.0
        hip_knee_ratio = -1.0

        if self.is_valid(side_pts.get("left_shoulder"), side_pts.get("right_shoulder")):
            sh_mid = self.midpoint(side_pts["left_shoulder"], side_pts["right_shoulder"])

        if self.is_valid(side_pts.get("left_hip"), side_pts.get("right_hip")):
            hip_mid = self.midpoint(side_pts["left_hip"], side_pts["right_hip"])

        if self.is_valid(side_pts.get("left_knee"), side_pts.get("right_knee")):
            knee_mid = self.midpoint(side_pts["left_knee"], side_pts["right_knee"])

        if self.is_valid(side_pts.get("left_ankle"), side_pts.get("right_ankle")):
            ankle_mid = self.midpoint(side_pts["left_ankle"], side_pts["right_ankle"])

        if sh_mid != [0.0, 0.0] and hip_mid != [0.0, 0.0]:
            cur_angle = self.angle(np.array(sh_mid) - np.array(hip_mid), [0, -1])

        if hip_mid != [0.0, 0.0] and knee_mid != [0.0, 0.0] and ankle_mid != [0.0, 0.0]:
            denom = max(0.01, ankle_mid[1] - knee_mid[1])
            hip_knee_ratio = (hip_mid[1] - knee_mid[1]) / denom

        elbow_flare = self.get_side_elbow_flare(side_pts)

        # ---------------------------
        # FRONT VIEW
        # ---------------------------
        k_dist = 0.0
        a_dist = 0.0
        s_dist_front = 0.0

        if self.is_valid(front_pts.get("left_knee"), front_pts.get("right_knee")):
            k_dist = self.dist_x(front_pts["left_knee"], front_pts["right_knee"])

        if self.is_valid(front_pts.get("left_ankle"), front_pts.get("right_ankle")):
            a_dist = self.dist_x(front_pts["left_ankle"], front_pts["right_ankle"])

        if self.is_valid(front_pts.get("left_shoulder"), front_pts.get("right_shoulder")):
            s_dist_front = self.dist_x(front_pts["left_shoulder"], front_pts["right_shoulder"])

        # ---------------------------
        # REP TRACKING
        # ---------------------------
        bar_y = sh_mid[1]

        if bar_y != 0.0:
            if self.standing_y is None or bar_y < self.standing_y:
                self.standing_y = bar_y

            if bar_y > (self.standing_y + self.rep_threshold):
                self.is_repping = True

                # Depth & Back Angle
                if hip_knee_ratio > self.max_hip_knee_ratio:
                    self.max_hip_knee_ratio = hip_knee_ratio
                    self.id_lowest_depth = frame_id

                if cur_angle > self.back_max:
                    self.back_max = cur_angle
                    self.id_max_angle = frame_id

                if cur_angle < self.back_min:
                    self.back_min = cur_angle
                    self.id_min_angle = frame_id

                # Forward Drift
                drift = sh_mid[0] - ankle_mid[0]
                if drift > self.max_fwd_drift:
                    self.max_fwd_drift = drift
                    self.id_max_fwd_drift = frame_id
                if drift < self.min_fwd_drift:
                    self.min_fwd_drift = drift
                    self.id_min_fwd_drift = frame_id

                # Knee Distance
                if k_dist > 0:
                    if k_dist > self.knee_dist_max:
                        self.knee_dist_max = k_dist
                        self.id_max_knee_dist = frame_id
                    if k_dist < self.knee_dist_min:
                        self.knee_dist_min = k_dist
                        self.id_min_knee_dist = frame_id
                    self.knee_dist_sum += k_dist
                    self.knee_dist_count += 1

                # Elbow Flare
                if elbow_flare > self.max_elbow_flare:
                    self.max_elbow_flare = elbow_flare
                    self.id_max_elbow_flare = frame_id
                if elbow_flare < self.min_elbow_flare:
                    self.min_elbow_flare = elbow_flare
                    self.id_min_elbow_flare = frame_id

                self.back_sum += cur_angle
                self.back_count += 1

            else:
                if self.is_repping:
                    rep_summary = {
                        "hip_knee_depth_ratio": to_float(round(self.max_hip_knee_ratio, 4)),
                        "max_back_angle": to_float(round(self.back_max, 2)),
                        "min_back_angle": to_float(round(self.back_min, 2)),
                        "back_angle_delta": to_float(round(self.back_max - self.back_min, 2)),
                        "max_forward_shoulder_drift": to_float(round(self.max_fwd_drift, 4)),
                        "min_forward_shoulder_drift": to_float(round(self.min_fwd_drift, 4)),
                        "foot_to_shoulder_ratio": to_float(round(a_dist / max(0.01, s_dist_front), 4)),
                        "knee_to_ankle_ratio": to_float(round(self.knee_dist_min / max(0.01, a_dist), 4)),
                        "max_knee_distance": to_float(round(self.knee_dist_max, 4)),
                        "min_knee_distance": to_float(round(self.knee_dist_min, 4)),
                        "avg_knee_distance": to_float(round(self.knee_dist_sum / max(1, self.knee_dist_count), 4)),
                        "max_elbow_flare": to_float(round(self.max_elbow_flare, 4)),
                        "min_elbow_flare": to_float(round(self.min_elbow_flare, 4)),
                        "elbow_flare_delta": to_float(round(self.max_elbow_flare - self.min_elbow_flare, 4)),
                        "event_frames": {
                            "lowest_depth": self.id_lowest_depth,
                            "max_back_angle": self.id_max_angle,
                            "min_back_angle": self.id_min_angle,
                            "max_fwd_drift": self.id_max_fwd_drift,
                            "min_fwd_drift": self.id_min_fwd_drift,
                            "max_knee_dist": self.id_max_knee_dist,
                            "min_knee_dist": self.id_min_knee_dist,
                            "max_elbow_flare": self.id_max_elbow_flare,
                            "min_elbow_flare": self.id_min_elbow_flare
                        }
                    }
                    self.reset_rep_metrics()
                    self.is_repping = False

        return (
            {
                "side": side_pts,
                "front": front_pts
            },
            "SUCCESS",
            metrics,
            {"position": bar_y},
            rep_summary
        )