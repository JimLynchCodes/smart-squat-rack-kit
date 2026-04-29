import time
import threading

import cv2

from cackle.models import FramePacket
from cackle.config import FRAME_WIDTH, FRAME_HEIGHT, FPS


class CameraWorker(threading.Thread):
    def __init__(self, name: str, index: int):
        super().__init__(daemon=True)
        self.name = name
        self.index = index
        self.cap = None
        self.running = False
        self.frame_id = 0
        self.latest = None
        self.lock = threading.Lock()

    def open(self) -> None:
        cap = cv2.VideoCapture(self.index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, FPS)

        if not cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.name} ({self.index})")

        self.cap = cap

    def run(self) -> None:
        self.open()
        self.running = True

        while self.running:
            ok, frame = self.cap.read()
            now_mono = time.monotonic()
            now_wall = time.time()

            packet = FramePacket(
                camera=self.name,
                frame_id=self.frame_id,
                ts_monotonic=now_mono,
                ts_wall=now_wall,
                width=frame.shape[1] if ok else 0,
                height=frame.shape[0] if ok else 0,
                ok=ok,
            )

            with self.lock:
                self.latest = (packet, frame if ok else None)

            self.frame_id += 1

    def get_latest(self):
        with self.lock:
            return self.latest

    def stop(self) -> None:
        self.running = False
        if self.cap:
            self.cap.release()