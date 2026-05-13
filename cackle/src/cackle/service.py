import signal
import time
import cv2

from cackle.camera import Camera
from cackle.config import *
from cackle.shared_ring import SharedFrame, SharedIndex
from cackle.publisher import Publisher

def run():
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    pub = Publisher(ZMQ_ADDR)

    print("\n" + "="*50)
    print(f"[cackle] INITIALIZING CAMERAS")
    print(f"  FRONT: Index {FRONT_CAM_INDEX} -> Targeting {FRONT_SHAPE[1]}x{FRONT_SHAPE[0]}")
    print(f"  SIDE : Index {SIDE_CAM_INDEX}  -> Targeting {SIDE_SHAPE[1]}x{SIDE_SHAPE[0]}")
    print("="*50 + "\n")

    # Initialize cameras with indices from config.py
    front_cam = Camera(FRONT_CAM_INDEX, FRONT_SHAPE[1], FRONT_SHAPE[0], FPS)
    side_cam = Camera(SIDE_CAM_INDEX, SIDE_SHAPE[1], SIDE_SHAPE[0], FPS)

    front_cam.open()
    side_cam.open()

    # Warmup and Verification
    # If Horus is silent, it's usually because we die here due to a bad index
    f_test = front_cam.read()
    s_test = side_cam.read()

    if f_test is None:
        print(f"[cackle] FATAL: FRONT camera (Index {FRONT_CAM_INDEX}) failed to read.")
        return
    if s_test is None:
        print(f"[cackle] FATAL: SIDE camera (Index {SIDE_CAM_INDEX}) failed to read.")
        return

    ACTUAL_FRONT_SHAPE = f_test.shape
    ACTUAL_SIDE_SHAPE = s_test.shape

    print(f"[cackle] HARDWARE READY")
    print(f"  FRONT ACTUAL: {ACTUAL_FRONT_SHAPE}")
    print(f"  SIDE  ACTUAL: {ACTUAL_SIDE_SHAPE}\n")

    # =====================================================
    # SHARED MEMORY (MUST EXIST FOR HORUS)
    # =====================================================
    front_buf = [
        SharedFrame(f"{FRONT_PREFIX}{i}", ACTUAL_FRONT_SHAPE, create=True)
        for i in range(RING_SIZE)
    ]

    side_buf = [
        SharedFrame(f"{SIDE_PREFIX}{i}", ACTUAL_SIDE_SHAPE, create=True)
        for i in range(RING_SIZE)
    ]

    index_shm = SharedIndex(FRAME_INDEX_NAME, create=True)
    frame_id_shm = SharedIndex(FRAME_ID_NAME, create=True)

    # Reset state
    index_shm.set(0)
    frame_id_shm.set(0)

    print("[cackle] SHM READY ✓")

    # =====================================================
    # MAIN LOOP
    # =====================================================
    frame_count = 0
    last_log = time.time()

    try:
        while running:
            f = front_cam.read()
            s = side_cam.read()

            if f is None or s is None:
                print("[cackle] WARNING: frame dropped from hardware")
                continue

            frame_count += 1

            # Update Frame IDs and Ring Slot
            fid = frame_id_shm.get() + 1
            frame_id_shm.set(fid)

            slot = fid % RING_SIZE
            index_shm.set(slot)

            # Write to respective SHM buffers
            front_buf[slot].write(f)
            side_buf[slot].write(s)

            # Signal to Horus and the Bridge
            pub.publish("frame.sync", {
                "frame_id": fid,
                "slot": slot,
            })

            # Heartbeat log
            if time.time() - last_log > 2.0:
                print(f"[cackle] alive | frame={fid} | slot={slot}")
                last_log = time.time()

            # Tight loop but yield to OS
            time.sleep(0.001)

    finally:
        print("\n[cackle] shutting down...")

        front_cam.close()
        side_cam.close()

        index_shm.unlink()
        frame_id_shm.unlink()

        for b in front_buf + side_buf:
            b.unlink()

        pub.close()