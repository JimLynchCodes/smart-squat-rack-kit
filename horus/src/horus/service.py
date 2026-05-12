import time
import json
from multiprocessing import shared_memory

import numpy as np

from horus.config import *
from horus.pipeline import SquatPipeline
from horus.publisher import Publisher
from horus.shared_ring import SharedIndex


# =========================================================
# LAZY SHARED FRAME (FIXES YOUR CRASH)
# =========================================================
class LazyFrame:
    def __init__(self, name, shape):
        self.name = name
        self.shape = shape
        self.shm = None
        self.buf = None

    def read(self):
        try:
            if self.shm is None:
                self.shm = shared_memory.SharedMemory(name=self.name)
                self.buf = np.ndarray(self.shape, dtype=np.uint8, buffer=self.shm.buf)

            return self.buf.copy()

        except FileNotFoundError:
            return None


# =========================================================
# ATTACH INDEX SAFELY
# =========================================================
def attach_index(name):
    while True:
        try:
            shm = shared_memory.SharedMemory(name=name)
            shm.close()
            return SharedIndex(name, create=False)
        except FileNotFoundError:
            print(f"[horus] waiting for index shm: {name}")
            time.sleep(0.2)


# =========================================================
# MAIN
# =========================================================
def run():

    print("[horus] starting...")

    pipeline = SquatPipeline()
    pub = Publisher(HORUS_PUB_ADDR)

    # -------------------------
    # SHARED MEMORY (SAFE ATTACH)
    # -------------------------
    index_shm = attach_index(FRAME_INDEX_NAME)
    frame_id_shm = attach_index(FRAME_ID_NAME)

    # IMPORTANT: lazy frames (NO PRE-ATTACH)
    front_ring = [
        LazyFrame(f"{FRONT_PREFIX}{i}", FRONT_SHAPE)
        for i in range(RING_SIZE)
    ]

    side_ring = [
        LazyFrame(f"{SIDE_PREFIX}{i}", SIDE_SHAPE)
        for i in range(RING_SIZE)
    ]

    print("[horus] attached (lazy mode) ✓")

    # -------------------------
    # MAIN LOOP
    # -------------------------
    try:
        while True:

            slot = index_shm.get()
            frame_id = frame_id_shm.get()

            front_img = front_ring[slot].read()
            side_img = side_ring[slot].read()

            # if frames not ready yet
            if front_img is None or side_img is None:
                print("[horus] waiting for frames...")
                time.sleep(0.01)
                continue

            # NOW PASSING frame_id INTO THE PIPELINE
            # AND UNPACKING ALL 5 RETURN VALUES
            pose, phase, metrics, bar, rep_summary = pipeline.process(
                front_img, 
                side_img,
                frame_id=frame_id
            )

            # LIVE DATA PAYLOAD
            payload = {
                "frame_id": frame_id,
                "phase": phase,
                "pose": pose,
                "instant_metrics": metrics,
                "bar": bar,
                "ts": time.time(),
            }

            # 1. PUBLISH LIVE STREAM
            pub.publish("pose.data", payload)

            # 2. PUBLISH REP SUMMARY ON COMPLETION
            if rep_summary:
                print(f"[horus] REP COMPLETED | ID: {frame_id}")
                pub.publish("rep.summary", rep_summary)

            # Log current frame status
            print(f"[horus] frame {frame_id} | slot {slot} | repping: {pipeline.is_repping}")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[horus] shutdown")

    finally:
        pub.close()