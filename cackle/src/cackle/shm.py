import numpy as np
from multiprocessing import shared_memory


class FrameSHM:
    def __init__(self, name: str, shape: tuple[int, int, int]):
        self.name = name
        self.shape = shape
        self.dtype = np.uint8

        size = int(np.prod(shape) * np.dtype(self.dtype).itemsize)

        try:
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=size)
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=name, create=False, size=size)

        self.buffer = np.ndarray(shape, dtype=self.dtype, buffer=self.shm.buf)

    def write(self, frame: np.ndarray):
        if frame.shape != self.shape:
            raise ValueError(f"shape mismatch {frame.shape} != {self.shape}")

        if frame.dtype != self.dtype:
            frame = frame.astype(self.dtype)

        self.buffer[:] = frame

    def close(self):
        self.shm.close()

    def unlink(self):
        self.shm.unlink()