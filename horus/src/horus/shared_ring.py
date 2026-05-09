import numpy as np
from multiprocessing import shared_memory


class SharedFrame:
    def __init__(self, name, shape, dtype=np.uint8, create=False):
        self.name = name
        self.shape = tuple(shape)
        self.dtype = dtype

        size = int(np.prod(self.shape)) * np.dtype(dtype).itemsize

        if create:
            try:
                old = shared_memory.SharedMemory(name=name)
                old.close()
                old.unlink()
            except FileNotFoundError:
                pass

            self.shm = shared_memory.SharedMemory(name=name, create=True, size=size)
        else:
            self.shm = shared_memory.SharedMemory(name=name)

        self.buf = np.ndarray(self.shape, dtype=dtype, buffer=self.shm.buf)

    def read(self):
        return self.buf.copy()

    def write(self, frame):
        self.buf[:] = frame

    def close(self):
        self.shm.close()

    def unlink(self):
        try:
            self.shm.unlink()
        except FileNotFoundError:
            pass


class SharedIndex:
    def __init__(self, name, create=False):
        self.name = name

        if create:
            try:
                old = shared_memory.SharedMemory(name=name)
                old.close()
                old.unlink()
            except FileNotFoundError:
                pass

            self.shm = shared_memory.SharedMemory(name=name, create=True, size=8)
            self.arr = np.ndarray((1,), dtype=np.int64, buffer=self.shm.buf)
            self.arr[0] = 0
        else:
            self.shm = shared_memory.SharedMemory(name=name)
            self.arr = np.ndarray((1,), dtype=np.int64, buffer=self.shm.buf)

    def get(self):
        return int(self.arr[0])

    def set(self, v):
        self.arr[0] = v

    def close(self):
        self.shm.close()

    def unlink(self):
        try:
            self.shm.unlink()
        except FileNotFoundError:
            pass