import numpy as np
from multiprocessing import shared_memory


import numpy as np
from multiprocessing import shared_memory

class SharedFrame:
    def __init__(self, name, shape, dtype=np.uint8, create=False):
        self.name = name
        self.shape = tuple(shape)
        self.dtype = dtype

        # Calculate required bytes
        size = int(np.prod(self.shape)) * np.dtype(dtype).itemsize

        if create:
            try:
                # Force cleanup of existing block to avoid size mismatches
                old = shared_memory.SharedMemory(name=name)
                old.close()
                old.unlink()
                print(f"[shm] cleaned up existing block: {name}")
            except FileNotFoundError:
                pass
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=size)
        else:
            self.shm = shared_memory.SharedMemory(name=name)

        # Safety Check: Does the block we attached to match the shape we want?
        if len(self.shm.buf) != size:
            actual_size = len(self.shm.buf)
            # This is where your previous crash happened. 
            # We raise a clearer error now.
            raise ValueError(
                f"SHM size mismatch for {name}. "
                f"Expected {size} bytes ({self.shape}), got {actual_size}."
            )

        self.buf = np.ndarray(self.shape, dtype=dtype, buffer=self.shm.buf)

    def read(self):
        return self.buf.copy()

    def write(self, frame):
        # Use [:] for in-place copy to existing memory buffer
        self.buf[:] = frame

    def close(self):
        self.shm.close()

    def unlink(self):
        try:
            self.shm.unlink()
        except (FileNotFoundError, AttributeError):
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