import numpy as np
from multiprocessing import shared_memory

class SharedFrame:
    def __init__(self, name: str, shape=(1080, 1920, 3), dtype=np.uint8, create=False):
        self.name = name
        self.shape = shape
        self.dtype = dtype
        self.expected_size = int(np.prod(shape)) * np.dtype(dtype).itemsize

        if create:
            try:
                old = shared_memory.SharedMemory(name=name)
                old.close()
                old.unlink()
            except FileNotFoundError:
                pass
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.expected_size)
        else:
            self.shm = shared_memory.SharedMemory(name=name)
            if self.shm.size < self.expected_size:
                actual = self.shm.size
                self.shm.close()
                raise ValueError(f"SHM SIZE MISMATCH: {name} is {actual}, need {self.expected_size}")

        self.buf = np.ndarray(shape, dtype=dtype, buffer=self.shm.buf)

    def write(self, frame):
        self.buf[:] = frame

    def read(self):
        return self.buf.copy()

    def close(self):
        if hasattr(self, 'shm'):
            self.shm.close()

    def unlink(self):
        try:
            self.shm.unlink()
        except FileNotFoundError:
            pass

class SharedIndex:
    """A shared 64-bit integer used to track the 'current' frame index in the ring."""
    def __init__(self, name: str, create=False):
        self.name = name
        self.size = 8  # 64-bit integer = 8 bytes

        if create:
            try:
                old = shared_memory.SharedMemory(name=name)
                old.close()
                old.unlink()
            except FileNotFoundError:
                pass
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.size)
            self.arr = np.ndarray((1,), dtype=np.int64, buffer=self.shm.buf)
            self.arr[0] = 0
        else:
            self.shm = shared_memory.SharedMemory(name=name)
            self.arr = np.ndarray((1,), dtype=np.int64, buffer=self.shm.buf)

    def get(self): 
        return int(self.arr[0])

    def set(self, v: int): 
        self.arr[0] = v

    def close(self):
        if hasattr(self, 'shm'):
            self.shm.close()

    def unlink(self):
        try:
            self.shm.unlink()
        except FileNotFoundError:
            pass