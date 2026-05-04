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

    print(f"[cackle] Initializing cameras...")

    # Camera(ID, Width, Height, FPS)
    # Note: We pass config intent, but hardware may override
    front_cam = Camera(0, FRONT_SHAPE[1], FRONT_SHAPE[0], FPS)
    side_cam = Camera(1, SIDE_SHAPE[1], SIDE_SHAPE[0], FPS)
  
    front_cam.open()
    side_cam.open()

    # Pre-read once to verify actual hardware resolution
    f_test = front_cam.read()
    s_test = side_cam.read()
  
    if f_test is None or s_test is None:
        print("[ERROR] Could not read from cameras. Check USB connections.")
        return

    # THE TRUTH: Get actual shapes from the hardware buffers
    ACTUAL_FRONT_SHAPE = f_test.shape
    ACTUAL_SIDE_SHAPE = s_test.shape

    print("\n" + "="*50)
    print("HARDWARE SYNC COMPLETE")
    print(f"FRONT: {ACTUAL_FRONT_SHAPE}")
    print(f"SIDE:  {ACTUAL_SIDE_SHAPE}")
    print("="*50 + "\n")

    # Create Shared Memory based on what the hardware IS, not what we WANT
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

    print("[cackle-service] online | publishing to frame.sync")

    try:
        while running:
            ts_sync = time.time()

            f = front_cam.read()
            ts_front = time.time() 

            s = side_cam.read()
            ts_side = time.time()  

            if f is None or s is None:
                continue

            fid = frame_id_shm.get() + 1
            frame_id_shm.set(fid)
          
            i = fid % RING_SIZE
            index_shm.set(i)

            front_buf[i].write(f)
            side_buf[i].write(s)

            # PAYLOAD: Pass 'shape' so Horus can dynamically adjust
            payload = {
                'frame_id': fid,
                'timestamp_sync': ts_sync,
                'active_buffer': i,
                'front': {
                    'shm': f"{FRONT_PREFIX}{i}",
                    'shape': ACTUAL_FRONT_SHAPE, # (H, W, C)
                    'timestamp': ts_front
                },
                'side': {
                    'shm': f"{SIDE_PREFIX}{i}",
                    'shape': ACTUAL_SIDE_SHAPE, # (H, W, C)
                    'timestamp': ts_side
                }
            }

            pub.publish("frame.sync", payload)
            print(f"[publishing...] topic: frame.sync | payload: {payload}")

            # Print status every 100 frames to keep the terminal clean
            if fid % 100 == 0:
                print(f"[cackle] Active: Frame {fid} | Slot {i}")

            time.sleep(0.001) # Maximize throughput

    finally:
        print("\n[cackle] Cleaning up resources...")
        front_cam.close()
        side_cam.close()
        index_shm.unlink()
        frame_id_shm.unlink()
        for b in front_buf + side_buf:
            b.unlink()
        pub.close()
        print("[cackle] Resources released.")

if __name__ == "__main__":
    run()