import cv2
import time
import zmq
import json

from horus.pipeline import SquatPipeline


def run():

    # ---------------------------
    # CAMERA (RESTORED)
    # ---------------------------
    cap = cv2.VideoCapture(0)  # 0 = default webcam

    if not cap.isOpened():
        print("[horus] ERROR: Cannot open camera")
        return

    # ---------------------------
    # PIPELINE
    # ---------------------------
    pipeline = SquatPipeline()

    # ---------------------------
    # ZMQ (ONLY FOR OUTPUT)
    # ---------------------------
    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    pub.bind("tcp://*:5556")

    print("[horus] online | reading camera directly...")

    frame_id = 0

    while True:

        ret, frame = cap.read()

        if not ret or frame is None:
            print("[horus] camera frame empty")
            continue

        # ---------------------------
        # RUN PIPELINE
        # ---------------------------
        front = None  # not used anymore
        side = frame

        pose, phase, metrics, bar = pipeline.process(front, side)

        if not pose:
            continue

        payload = {
            "frame_id": frame_id,
            "pose": pose,
            "rep_phase": phase,
            "instant_metrics": metrics,
            "bar": bar,
            "ts": time.time()
        }

        # ---------------------------
        # SEND TO SENSEI
        # ---------------------------
        pub.send_multipart([
            b"pose.data",
            json.dumps(payload).encode()
        ])

        frame_id += 1

        # optional debug
        print(f"[horus] frame {frame_id} | {phase}")

        # small sleep to reduce CPU burn
        time.sleep(0.01)