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

    def midpoint(self, a, b):
        return [(a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5]

    def is_valid(self, *pts):
        """Returns True only if ALL provided points are detected (not [0,0])."""
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
        """Maps all 17 YOLO points. Ignores points with low confidence."""
        if results.keypoints is None or len(results.keypoints.data) == 0:
            return {}
        
        # xyn: normalized coordinates [N, 17, 2]
        # conf: confidence scores [N, 17]
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
            # Check if the model is confident enough about this specific point
            if idx < len(kp) and conf[idx] > threshold:
                res[name] = kp[idx].tolist()
            else:
                # If not in frame or low confidence, treat as non-existent
                res[name] = [0.0, 0.0]
                
        return res

    def process(self, front_img, side_img):
        # 1. Inference
        side_res = self.model(side_img, verbose=False)[0] if side_img is not None else None
        front_res = self.model(front_img, verbose=False)[0] if front_img is not None else None

        # 2. Keypoint Extraction (Full 17 points for both)
        side_pts = self.extract_keypoints(side_res) if side_res else {}
        front_pts = self.extract_keypoints(front_res) if front_res else {}

        if not side_pts and not front_pts:
            return {}, "NO_PERSON", {}, {}

        # 3. Metrics Calculation (Strict Validation)
        metrics = {"side": {}, "front": {}}
        
        # SIDE: Back Angle
        if self.is_valid(side_pts.get("left_shoulder"), side_pts.get("right_shoulder"), 
                        side_pts.get("left_hip"), side_pts.get("right_hip")):
            sh_mid = self.midpoint(side_pts["left_shoulder"], side_pts["right_shoulder"])
            hip_mid = self.midpoint(side_pts["left_hip"], side_pts["right_hip"])
            metrics["side"]["back_angle"] = to_float(round(self.angle(np.array(sh_mid) - np.array(hip_mid), [0, -1]), 2))
        else:
            sh_mid = [0.0, 0.0] # Needed for bar calc below

        # SIDE: Knee Angle
        if self.is_valid(side_pts.get("left_hip"), side_pts.get("left_knee"), side_pts.get("left_ankle")):
            k_ang = self.angle(
                np.array(side_pts["left_hip"]) - np.array(side_pts["left_knee"]),
                np.array(side_pts["left_ankle"]) - np.array(side_pts["left_knee"])
            )
            metrics["side"]["knee_angle"] = to_float(round(k_ang, 2))

        # SIDE: Forearm Angle
        if self.is_valid(side_pts.get("left_elbow"), side_pts.get("left_wrist")):
            f_ang = self.angle(np.array(side_pts["left_wrist"]) - np.array(side_pts["left_elbow"]), [0, -1])
            metrics["side"]["forearm_angle"] = to_float(round(f_ang, 2))

        # FRONT: Knee Valgus
        if self.is_valid(front_pts.get("left_knee"), front_pts.get("right_knee")):
            valgus = abs(front_pts["left_knee"][0] - front_pts["right_knee"][0])
            metrics["front"]["knee_valgus"] = to_float(round(valgus, 4))

        # 4. Bar / Velocity (Calculated using side shoulder midpoint)
        now = time.time()
        bar_y = sh_mid[1]
        vel_y = 0.0

        if self.prev_ts and bar_y != 0.0:
            dt = now - self.prev_ts
            if dt > 0:
                vel_y = (bar_y - self.prev_bar_y) / dt

        if bar_y != 0.0:
            self.prev_ts = now
            self.prev_bar_y = bar_y

        # 5. Final Output
        pose = {
            "side": side_pts,
            "front": front_pts
        }

        bar = {
            "velocity_y": to_float(vel_y),
            "position": to_float(bar_y),
        }

        return pose, "SUCCESS", metrics, bar