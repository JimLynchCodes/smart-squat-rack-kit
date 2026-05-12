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
        
        # Rep State Tracking
        self.standing_y = None
        self.is_repping = False
        self.rep_threshold = 0.05
        
        # Running Metric Variables
        self.back_min = float('inf')
        self.back_max = float('-inf')
        self.back_sum = 0.0
        self.back_count = 0
        self.lowest_hip_depth = 0.0

        # Frame ID Tracking
        self.id_max_angle = None
        self.id_min_angle = None
        self.id_lowest_depth = None

    def midpoint(self, a, b):
        return [(a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5]

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
        
        mapping = {
            "nose": 0, "left_eye": 1, "right_eye": 2, "left_ear": 3, "right_ear": 4,
            "left_shoulder": 5, "right_shoulder": 6, "left_elbow": 7, "right_elbow": 8,
            "left_wrist": 9, "right_wrist": 10, "left_hip": 11, "right_hip": 12,
            "left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16
        }
        
        res = {}
        for name, idx in mapping.items():
            if idx < len(kp) and conf[idx] > threshold:
                res[name] = kp[idx].tolist()
            else:
                res[name] = [0.0, 0.0]
        return res

    def reset_rep_metrics(self):
        self.back_min = float('inf')
        self.back_max = float('-inf')
        self.back_sum = 0.0
        self.back_count = 0
        self.lowest_hip_depth = 0.0
        self.id_max_angle = None
        self.id_min_angle = None
        self.id_lowest_depth = None

    def process(self, front_img, side_img, frame_id=None):
        side_res = self.model(side_img, verbose=False)[0] if side_img is not None else None
        front_res = self.model(front_img, verbose=False)[0] if front_img is not None else None

        side_pts = self.extract_keypoints(side_res) if side_res else {}
        front_pts = self.extract_keypoints(front_res) if front_res else {}

        if not side_pts and not front_pts:
            return {}, "NO_PERSON", {}, {}, None

        metrics = {"side": {}, "front": {}}
        rep_summary = None
        
        sh_mid = [0.0, 0.0]
        hip_mid = [0.0, 0.0]
        cur_angle = 0.0

        if self.is_valid(side_pts.get("left_shoulder"), side_pts.get("right_shoulder")):
            sh_mid = self.midpoint(side_pts["left_shoulder"], side_pts["right_shoulder"])
        
        if self.is_valid(side_pts.get("left_hip"), side_pts.get("right_hip")):
            hip_mid = self.midpoint(side_pts["left_hip"], side_pts["right_hip"])
            metrics["side"]["current_hip_depth"] = to_float(round(hip_mid[1], 4))

        if sh_mid != [0.0, 0.0] and hip_mid != [0.0, 0.0]:
            cur_angle = self.angle(np.array(sh_mid) - np.array(hip_mid), [0, -1])

        # Rep Tracking Logic
        bar_y = sh_mid[1]
        if bar_y != 0.0:
            if self.standing_y is None or bar_y < self.standing_y:
                self.standing_y = bar_y

            if bar_y > (self.standing_y + self.rep_threshold):
                self.is_repping = True
                
                # Tracking by Frame ID
                if hip_mid[1] > self.lowest_hip_depth:
                    self.lowest_hip_depth = hip_mid[1]
                    self.id_lowest_depth = frame_id

                if cur_angle > self.back_max:
                    self.back_max = cur_angle
                    self.id_max_angle = frame_id

                if cur_angle < self.back_min:
                    self.back_min = cur_angle
                    self.id_min_angle = frame_id

                self.back_sum += cur_angle
                self.back_count += 1
            else:
                if self.is_repping:
                    rep_summary = {
                        "lowest_hip_depth": to_float(round(self.lowest_hip_depth, 4)),
                        "max_back_angle": to_float(round(self.back_max, 2)),
                        "min_back_angle": to_float(round(self.back_min, 2)),
                        "avg_back_angle": to_float(round(self.back_sum / max(1, self.back_count), 2)),
                        "event_frames": {
                            "lowest_depth": self.id_lowest_depth,
                            "max_back_angle": self.id_max_angle,
                            "min_back_angle": self.id_min_angle
                        }
                    }
                    self.reset_rep_metrics()
                    self.is_repping = False

        metrics["side"].update({
            "back_angle": to_float(round(cur_angle, 2)),
            "back_angle_min": to_float(round(self.back_min, 2)) if self.back_min != float('inf') else 0.0,
            "back_angle_max": to_float(round(self.back_max, 2)) if self.back_max != float('-inf') else 0.0,
            "back_angle_avg": to_float(round(self.back_sum / max(1, self.back_count), 2)),
            "lowest_hip_depth": to_float(round(self.lowest_hip_depth, 4)),
            "lowest_hip_depth_frame_id": self.id_lowest_depth,
            "max_back_angle_frame_id": self.id_max_angle,
            "min_back_angle_frame_id": self.id_min_angle
        })

        now = time.time()
        vel_y = 0.0
        if self.prev_ts and bar_y != 0.0:
            dt = now - self.prev_ts
            if dt > 0: vel_y = (bar_y - self.prev_bar_y) / dt
        if bar_y != 0.0:
            self.prev_ts, self.prev_bar_y = now, bar_y

        return {"side": side_pts, "front": front_pts}, "SUCCESS", metrics, {"velocity_y": vel_y, "position": bar_y}, rep_summary