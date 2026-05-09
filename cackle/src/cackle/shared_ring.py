import numpy as np
from multiprocessing import shared_memory


class SharedFrame:
    """
    Shared memory frame buffer for video frames.

    Supports dynamic resolution per instance.
    Safe for OpenCV + YOLO pipelines.
    """

    def __init__(self, name: str, shape, dtype=np.uint8, create=False):
        self.name = name
        self.shape = tuple(shape)
        self.dtype = dtype

        self.expected_size = int(np.prod(self.shape)) * np.dtype(dtype).itemsize

        if create:
            # cleanup stale shm if exists
            try:
                old = shared_memory.SharedMemory(name=name)
                old.close()
                old.unlink()
            except FileNotFoundError:
                pass

            self.shm = shared_memory.SharedMemory(
                name=name,
                create=True,
                size=self.expected_size
            )
        else:
            self.shm = shared_memory.SharedMemory(name=name)

            if self.shm.size < self.expected_size:
                actual = self.shm.size
                self.shm.close()
                raise ValueError(
                    f"[SHM ERROR] {name}: size mismatch "
                    f"(got {actual}, expected {self.expected_size})"
                )

        self.buf = np.ndarray(
            self.shape,
            dtype=self.dtype,
            buffer=self.shm.buf
        )

    # -------------------------
    # WRITE (CACKLE SIDE)
    # -------------------------
    def write(self, frame):
        """
        Writes frame into shared memory safely.
        Handles non-contiguous OpenCV arrays.
        """
        if frame is None:
            return

        frame = np.ascontiguousarray(frame)

        if frame.shape != self.shape:
            raise ValueError(
                f"[SHM WRITE ERROR] Shape mismatch: "
                f"got {frame.shape}, expected {self.shape}"
            )

        self.buf[:] = frame

    # -------------------------
    # READ (HORUS SIDE)
    # -------------------------
    def read(self):
        """
        Returns a COPY of the frame (safe for YOLO inference).
        """
        return self.buf.copy()

    # -------------------------
    # CLEANUP
    # -------------------------
    def close(self):
        if hasattr(self, "shm"):
            self.shm.close()

    def unlink(self):
        try:
            self.shm.unlink()
        except FileNotFoundError:
            pass


class SharedIndex:
    """
    Shared integer index for ring buffer coordination.
    """

    def __init__(self, name: str, create=False):
        self.name = name
        self.size = 8  # int64

        if create:
            try:
                old = shared_memory.SharedMemory(name=name)
                old.close()
                old.unlink()
            except FileNotFoundError:
                pass

            self.shm = shared_memory.SharedMemory(
                name=name,
                create=True,
                size=self.size
            )

            self.arr = np.ndarray((1,), dtype=np.int64, buffer=self.shm.buf)
            self.arr[0] = 0
        else:
            self.shm = shared_memory.SharedMemory(name=name)
            self.arr = np.ndarray((1,), dtype=np.int64, buffer=self.shm.buf)

    # -------------------------
    def get(self):
        return int(self.arr[0])

    def set(self, v: int):
        self.arr[0] = int(v)

    def close(self):
        if hasattr(self, "shm"):
            self.shm.close()

    def unlink(self):
        try:
            self.shm.unlink()
        except FileNotFoundError:
            pass