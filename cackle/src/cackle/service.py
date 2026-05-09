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

    print("[cackle] starting cameras...")

    front_cam = Camera(0, FRONT_SHAPE[1], FRONT_SHAPE[0], FPS)
    side_cam = Camera(1, SIDE_SHAPE[1], SIDE_SHAPE[0], FPS)

    front_cam.open()
    side_cam.open()

    # warmup
    f_test = front_cam.read()
    s_test = side_cam.read()

    if f_test is None or s_test is None:
        print("[cackle] ERROR: camera init failed")
        return

    ACTUAL_FRONT_SHAPE = f_test.shape
    ACTUAL_SIDE_SHAPE = s_test.shape

    print("\n==============================")
    print("[cackle] SHM INIT")
    print("FRONT:", ACTUAL_FRONT_SHAPE)
    print("SIDE :", ACTUAL_SIDE_SHAPE)
    print("==============================\n")

    # =====================================================
    # SHARED MEMORY (THIS MUST EXIST BEFORE HORUS STARTS)
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

    # reset state
    index_shm.set(0)
    frame_id_shm.set(0)

    print("[cackle] SHM READY ✓")

    # =====================================================
    # DEBUG: VERIFY SHM IS REAL IN OS
    # =====================================================
    from multiprocessing import shared_memory

    try:
        shm = shared_memory.SharedMemory(name=FRAME_INDEX_NAME)
        shm.close()
        print("[cackle] VERIFIED: index visible in OS")
    except FileNotFoundError:
        print("[cackle] FATAL: index NOT visible (SHM broken)")
        return

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
                print("[cackle] WARNING: frame dropped")
                continue

            frame_count += 1

            fid = frame_id_shm.get() + 1
            frame_id_shm.set(fid)

            slot = fid % RING_SIZE
            index_shm.set(slot)

            front_buf[slot].write(f)
            side_buf[slot].write(s)

            pub.publish("frame.sync", {
                "frame_id": fid,
                "slot": slot,
            })

            # heartbeat log
            if time.time() - last_log > 2.0:
                print(f"[cackle] alive | frame={fid}")
                last_log = time.time()

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