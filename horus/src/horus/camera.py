import cv2


class CameraInput:
    """
    Direct dual-camera reader.

    Front + side camera feeds are captured locally in Horus.
    This removes the need for Cackle/ZMQ frame transport.
    """

    def __init__(self, front_id=0, side_id=1):
        self.front_cap = cv2.VideoCapture(front_id)
        self.side_cap = cv2.VideoCapture(side_id)

        if not self.front_cap.isOpened():
            print("[camera] WARNING: Front camera not opened")

        if not self.side_cap.isOpened():
            print("[camera] WARNING: Side camera not opened")

    def read(self):
        ret_f, front = self.front_cap.read()
        ret_s, side = self.side_cap.read()

        if not ret_f or not ret_s:
            return None, None

        return front, side