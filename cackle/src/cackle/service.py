import signal
import time
from cackle.camera import Camera
from cackle.config import *
from cackle.shared_ring import SharedFrame, SharedIndex
from cackle.publisher import Publisher


def run():
   running = True


   def stop(*_):
       nonlocal running
       running = False


   signal.signal(signal.SIGINT, stop)
   signal.signal(signal.SIGTERM, stop)


   pub = Publisher(ZMQ_ADDR)


   # Note: Camera init uses (width, height)
   front_cam = Camera(0, FRONT_SHAPE[1], FRONT_SHAPE[0], FPS)
   side_cam = Camera(1, SIDE_SHAPE[1], SIDE_SHAPE[0], FPS)
  
   front_cam.open()
   side_cam.open()


   # Pre-read once to verify actual hardware resolution
   f_test = front_cam.read()
   s_test = side_cam.read()
  
   if f_test is None or s_test is None:
       print("[ERROR] Could not read from cameras.")
       return


   ACTUAL_FRONT_SHAPE = f_test.shape
   ACTUAL_SIDE_SHAPE = s_test.shape


   front_buf = [SharedFrame(f"{FRONT_PREFIX}{i}", ACTUAL_FRONT_SHAPE, create=True) for i in range(RING_SIZE)]
   side_buf = [SharedFrame(f"{SIDE_PREFIX}{i}", ACTUAL_SIDE_SHAPE, create=True) for i in range(RING_SIZE)]
  
   index_shm = SharedIndex(FRAME_INDEX_NAME, create=True)
   frame_id_shm = SharedIndex(FRAME_ID_NAME, create=True)


   print("[cackle-service] running | Metadata Timestamps Enabled")


   try:
       while running:
           # Capture global start time for this sync pair
           ts_sync = time.time()


           f = front_cam.read()
           ts_front = time.time() # Precise moment front frame was finished reading


           s = side_cam.read()
           ts_side = time.time()  # Precise moment side frame was finished reading


           if f is None or s is None:
               continue


           fid = frame_id_shm.get() + 1
           frame_id_shm.set(fid)
          
           i = fid % RING_SIZE
           index_shm.set(i)


           front_buf[i].write(f)
           side_buf[i].write(s)


           payload = {
               'frame_id': fid,
               'timestamp_sync': ts_sync,
               'active_buffer': i,
               'front': {
                   'camera': 'front',
                   'frame_id': fid,
                   'shm': f"{FRONT_PREFIX}{i}",
                   'timestamp': ts_front
               },
               'side': {
                   'camera': 'side',
                   'frame_id': fid,
                   'shm': f"{SIDE_PREFIX}{i}",
                   'timestamp': ts_side
               }
           }


           print(f"[publishing...] topic: frame.sync | payload: {payload}")
           pub.publish("frame.sync", payload)


           time.sleep(0.01)


   finally:
       print("\n[cackle] Cleaning up resources...")
       front_cam.close()
       side_cam.close()
       index_shm.unlink()
       frame_id_shm.unlink()
       for b in front_buf + side_buf:
           b.unlink()
       pub.close()
       print("[cackle] Resources released.")