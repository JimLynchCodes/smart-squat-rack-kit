import signal
import time

from cackle.camera import CameraWorker
from cackle.publisher import Publisher
from cackle.shm import FrameSHM
from cackle.double_buffer import DoubleBufferState
from cackle.config import (
    FRONT_CAM_INDEX,
    SIDE_CAM_INDEX,
    PUB_ADDR,
    FRONT_FRAME_SHAPE,
    SIDE_FRAME_SHAPE,
)


def run() -> None:
    running = True

    def handle(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGTERM, handle)

    # -------------------------
    # cameras
    # -------------------------
    front = CameraWorker("front", FRONT_CAM_INDEX)
    side = CameraWorker("side", SIDE_CAM_INDEX)

    # -------------------------
    # shared memory (double buffer)
    # -------------------------
    front_a = FrameSHM("cackle_front_a", FRONT_FRAME_SHAPE)
    front_b = FrameSHM("cackle_front_b", FRONT_FRAME_SHAPE)

    side_a = FrameSHM("cackle_side_a", SIDE_FRAME_SHAPE)
    side_b = FrameSHM("cackle_side_b", SIDE_FRAME_SHAPE)

    buffer_state = DoubleBufferState()

    # -------------------------
    # event bus
    # -------------------------
    pub = Publisher(PUB_ADDR)

    front.start()
    side.start()

    print("[cackle] LEVEL 2 active (double-buffer + shm + sync)")

    frame_id = 0

    try:
        while running:
            front_data = front.get_latest()
            side_data = side.get_latest()

            if not front_data or not side_data:
                time.sleep(0.01)
                continue

            front_packet, front_frame = front_data
            side_packet, side_frame = side_data

            # -------------------------
            # WRITE FIRST (IMPORTANT)
            # -------------------------
            if buffer_state.active == "a":
                front_a.write(front_frame)
                side_a.write(side_frame)
            else:
                front_b.write(front_frame)
                side_b.write(side_frame)

            # -------------------------
            # FLIP AFTER WRITE
            # -------------------------
            active = buffer_state.flip()

            # -------------------------
            # PUBLISH EVENT
            # -------------------------
            pub.publish(
                "frame.sync",
                {
                    "frame_id": frame_id,
                    "active_buffer": active,
                    "front": {
                        "camera": "front",
                        "frame_id": front_packet.frame_id,
                        "shm": f"cackle_front_{active}",
                    },
                    "side": {
                        "camera": "side",
                        "frame_id": side_packet.frame_id,
                        "shm": f"cackle_side_{active}",
                    },
                },
            )

            print(f"[cackle] frame.sync {frame_id} buffer={active}")

            frame_id += 1
            time.sleep(0.01)

    finally:
        print("[cackle] shutting down")

        front.stop()
        side.stop()

        for shm in [front_a, front_b, side_a, side_b]:
            shm.close()
            try:
                shm.unlink()
            except FileNotFoundError:
                pass

        pub.close()