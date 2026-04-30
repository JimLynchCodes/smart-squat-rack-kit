import json
import signal
import time

from horus.config import FRAME_SYNC_ADDR, FRONT_SHAPE, SIDE_SHAPE
from horus.zmq_client import FrameSubscriber
from horus.shm import SharedFrame
from horus.pipeline import HorusPipeline


def main():
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    sub = FrameSubscriber(FRAME_SYNC_ADDR)
    pipeline = HorusPipeline()

    print("[horus] online")

    while running:
        msg = sub.recv()
        payload = json.loads(msg.decode("utf-8"))

        buffer = payload["active_buffer"]

        front_name = f"cackle_front_{buffer}"
        side_name = f"cackle_side_{buffer}"

        front = SharedFrame(front_name, FRONT_SHAPE)
        side = SharedFrame(side_name, SIDE_SHAPE)

        try:
            front_frame = front.read()
            side_frame = side.read()

            result = pipeline.process(
                frame_id=payload["frame_id"],
                front_frame=front_frame,
                side_frame=side_frame,
            )

            print(
                f"[horus] "
                f"frame={result['frame_id']} "
                f"phase={result['rep_phase']:<7} "
                f"knee={result['metrics']['knee_angle_proxy']:.1f} "
                f"hip={result['metrics']['hip_height']:.2f} "
                f"back={result['metrics']['back_angle']:.1f} "
                f"knee_track={result['metrics']['knee_track']:+.3f} "
                f"bar_dx={result['bar']['path_dx']:+.3f}"
            )

        finally:
            front.close()
            side.close()

        time.sleep(0.001)


if __name__ == "__main__":
    main()