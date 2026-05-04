import time
import json
import zmq
import sys
import numpy as np
from horus.config import *
from horus.pipeline import SquatPipeline
from horus.shm import SharedFrame

class HorusComms:
    def __init__(self):
        self.ctx = zmq.Context()
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(CACKLE_ZMQ_ENDPOINT)
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "frame.sync")
        
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(HORUS_ZMQ_ADDR)

def run():
    print("[horus] starting dynamic service...")
    
    pipeline = SquatPipeline()
    comms = HorusComms()
    shm_cache = {}

    print("[horus] online. waiting for frame.sync events...")

    try:
        while True:
            try:
                topic, payload = comms.sub.recv_multipart(flags=zmq.NOBLOCK)
                meta = json.loads(payload.decode())
            except zmq.Again:
                time.sleep(0.001)
                continue

            views = {'front': meta['front'], 'side': meta['side']}
            frames = {}

            # 1. Sync Shared Memory
            for view_name, data in views.items():
                shm_name = data['shm']
                target_shape = tuple(data['shape']) 

                if shm_name not in shm_cache or shm_cache[shm_name].shape != target_shape:
                    print(f"[horus] Mapping {shm_name} with shape {target_shape}")
                    if shm_name in shm_cache:
                        shm_cache[shm_name].close()
                    shm_cache[shm_name] = SharedFrame(shm_name, target_shape)

                frames[view_name] = shm_cache[shm_name].read()

            # 2. Process AI Pipeline
            pose, phase, metrics, bar = pipeline.process(frames['front'], frames['side'])

            # 3. Construct the comprehensive payload (Define 'out' first!)
            out = {
                "frame_id": meta['frame_id'],
                "pose": {
                    "left_hip": pose.get("left_hip"),
                    "right_hip": pose.get("right_hip"),
                    "hips_midpoint": pose.get("hips_midpoint"),
                    "left_knee": pose.get("left_knee"),
                    "right_knee": pose.get("right_knee"),
                    "knees_midpoint": pose.get("knees_midpoint"),
                    "left_ankle": pose.get("left_ankle"),
                    "right_ankle": pose.get("right_ankle"),
                    "ankles_midpoint": pose.get("ankles_midpoint"),
                    "left_shoulder": pose.get("left_shoulder"),
                    "right_shoulder": pose.get("right_shoulder"),
                    "shoulders_midpoint": pose.get("shoulders_midpoint"),
                    "score": pose.get("score", 0.0)
                },
                "direction": pose.get("direction", "UNKNOWN"),
                "rep_phase": phase,
                "instant_metrics": {
                    "back_angle": metrics.get("back_angle"),
                    "knee_angle_proxy": metrics.get("knee_angle_proxy"),
                    "knee_dist": metrics.get("knees_distance"),
                    "hip_y": metrics.get("hip_y"),
                    "depth_relative_to_knee": metrics.get("depth_relative_to_knee")
                },
                "bar": {
                    "position": bar.get("position"),
                    "velocity_y": bar.get("velocity_y"),
                    "acceleration_y": bar.get("acceleration_y")
                },
                "ts_cackle": meta['timestamp_sync'],
                "ts_horus": time.time()
            }

            # 4. Debug Output (Every 100 frames)
            if meta['frame_id'] % 100 == 0:
                print(f"\n--- [horus] Frame {meta['frame_id']} Metrics ---")
                print(json.dumps(out, indent=2))
                print("-" * 30)

            # 5. Publish to Sensei
            comms.pub.send_multipart([b"pose.data", json.dumps(out).encode()])

    except KeyboardInterrupt:
        print("\n[horus] shutting down...")
    finally:
        for shm in shm_cache.values():
            shm.close()
        print("[horus] cleaned up.")

if __name__ == "__main__":
    run()