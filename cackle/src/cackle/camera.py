import cv2


class Camera:
   def __init__(self, index: int, width: int, height: int, fps: int):
       self.index = index
       self.width = width
       self.height = height
       self.fps = fps
       self.cap = None


   def open(self):
       self.cap = cv2.VideoCapture(self.index)
       self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
       self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
       self.cap.set(cv2.CAP_PROP_FPS, self.fps)


       if not self.cap.isOpened():
           raise RuntimeError(f"Failed to open camera {self.index}")


   def read(self):
       if self.cap is None:
           return None
       ok, frame = self.cap.read()
       return frame if ok else None


   def close(self):
       if self.cap:
           self.cap.release()
           self.cap = None