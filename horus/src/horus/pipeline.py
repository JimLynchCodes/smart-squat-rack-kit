import numpy as np
import time
from ultralytics import YOLO

class SquatPipeline:
    def __init__(self):
        # Load YOLOv8 Pose model (n is fastest, m/l are more accurate)
        # It will auto-download the .pt file on first run
        self.model = YOLO('yolov8n-pose.pt') 
        
        # Tracking state for velocity/acceleration
        self.prev_bar_y = None
        self.prev_ts = None
        self.prev_velocity = 0

    def process(self, front_img, side_img):
        # 1. RUN INFERENCE
        # We focus on the side_img for the heavy lifting of squat mechanics
        # side_img should be (720, 1280, 3) based on your hardware log
        results = self.model(side_img, verbose=False, stream=False)[0]
        
        if not results.keypoints or len(results.keypoints.data) == 0:
            return {}, "NO_PERSON", {}, {}

        # 2. EXTRACT KEYPOINTS (YOLO index mapping)
        # 5: L shoulder, 6: R shoulder, 11: L hip, 12: R hip, 13: L knee, 14: R knee, 15: L ankle, 16: R ankle
        kp = results.keypoints.xyn[0].cpu().numpy() # Normalized coordinates [0, 1]
        
        def get_kp(idx):
            return kp[idx].tolist() if len(kp) > idx else [0, 0]

        l_hip, r_hip = get_kp(11), get_kp(12)
        l_knee, r_knee = get_kp(13), get_kp(14)
        l_ankle, r_ankle = get_kp(15), get_kp(16)
        l_shld, r_shld = get_kp(5), get_kp(6)

        # 3. CALCULATE MIDPOINTS & GEOMETRY
        def midpoint(p1, p2):
            return [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]

        hip_mid = midpoint(l_hip, r_hip)
        knee_mid = midpoint(l_knee, r_knee)
        ankle_mid = midpoint(l_ankle, r_ankle)
        shld_mid = midpoint(l_shld, r_shld)

        # 4. MATH: ANGLES & VELOCITY
        # Knee angle (Hip-Knee-Ankle)
        ba = np.array(l_hip) - np.array(l_knee)
        bc = np.array(l_ankle) - np.array(l_knee)
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        knee_angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

        # Back Angle (Shoulder to Hip vs Vertical)
        back_vector = np.array(shld_mid) - np.array(hip_mid)
        back_angle = np.degrees(np.arctan2(abs(back_vector[0]), abs(back_vector[1])))

        # 5. BAR TRACKING (Assuming bar is at shoulder midpoint for back squat)
        now = time.time()
        bar_pos = shld_mid
        vel_y = 0
        accel_y = 0

        if self.prev_bar_y is not None and self.prev_ts is not None:
            dt = now - self.prev_ts
            vel_y = (bar_pos[1] - self.prev_bar_y) / dt
            accel_y = (vel_y - self.prev_velocity) / dt
        
        self.prev_bar_y = bar_pos[1]
        self.prev_ts = now
        self.prev_velocity = vel_y

        # 6. PACKAGING
        pose = {
            "left_hip": l_hip, "right_hip": r_hip, "hips_midpoint": hip_mid,
            "left_knee": l_knee, "right_knee": r_knee, "knees_midpoint": knee_mid,
            "left_ankle": l_ankle, "right_ankle": r_ankle, "ankles_midpoint": ankle_mid,
            "left_shoulder": l_shld, "right_shoulder": r_shld, "shoulders_midpoint": shld_mid,
            "score": float(results.probs) if results.probs else 0.9,
            "direction": "LEFT" if l_shld[0] < r_shld[0] else "RIGHT"
        }

        metrics = {
            "back_angle": round(back_angle, 2),
            "knee_angle_proxy": round(knee_angle, 2),
            "knees_distance": abs(l_knee[0] - r_knee[0]),
            "hip_y": round(hip_mid[1], 4),
            "depth_relative_to_knee": round(knee_mid[1] - hip_mid[1], 4)
        }

        # Determine Phase
        phase = "DESCENT" if vel_y > 0.01 else "ASCENT" if vel_y < -0.01 else "STARKED"

        bar = {
            "position": bar_pos,
            "velocity_y": round(vel_y, 4),
            "acceleration_y": round(accel_y, 4)
        }

        return pose, phase, metrics, bar