from multiprocessing import shared_memory
import numpy as np


class SharedFrame:
   def __init__(self, name: str, shape, dtype=np.uint8, create=False):
       self.name = name
       self.shape = shape
       self.size = int(np.prod(shape))


       if create:
           try:
               old = shared_memory.SharedMemory(name=name)
               old.close()
               old.unlink()
           except FileNotFoundError:
               pass
           self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.size)
       else:
           self.shm = shared_memory.SharedMemory(name=name)


       self.buf = np.ndarray(shape, dtype=dtype, buffer=self.shm.buf)


   def write(self, frame):
       self.buf[:] = frame


   def read(self):
       return self.buf


   def close(self):
       self.shm.close()


   def unlink(self):
       try:
           self.shm.unlink()
       except FileNotFoundError:
           pass


class SharedIndex:
   def __init__(self, name: str, create=False):
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


   def get(self): return int(self.arr[0])
   def set(self, v: int): self.arr[0] = v
   def close(self): self.shm.close()
   def unlink(self):
       try:
           self.shm.unlink()
       except FileNotFoundError:
           pass