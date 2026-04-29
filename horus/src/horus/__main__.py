import json
import signal
import time

from horus.config import FRAME_SYNC_ADDR
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

    front_cache = None
    side_cache = None

    print("[horus] running")

    while running:
        msg = sub.recv()
        payload = json.loads(msg.decode())

        buffer = payload["active_buffer"]

        front_name = f"cackle_front_{buffer}"
        side_name = f"cackle_side_{buffer}"

        # attach correct buffer
        front = SharedFrame(front_name, (1080, 1920, 3))
        side = SharedFrame(side_name, (720, 1280, 3))

        front_frame = front.read()

        result = pipeline.process(payload["frame_id"], front_frame)

        print(
            f"[horus] frame={result['frame_id']} "
            f"phase={result['phase']} "
            f"knee={result['metrics']['knee_angle_proxy']:.1f}"
        )

        front.close()
        side.close()

        time.sleep(0.001)


if __name__ == "__main__":
    main()