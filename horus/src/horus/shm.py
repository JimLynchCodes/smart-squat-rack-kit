import numpy as np
from multiprocessing import shared_memory


class SharedFrame:
    def __init__(self, name: str, shape: tuple):
        self.shm = shared_memory.SharedMemory(name=name)
        self.frame = np.ndarray(shape, dtype=np.uint8, buffer=self.shm.buf)

    def read(self):
        return self.frame.copy()

    def close(self):
        self.shm.close()