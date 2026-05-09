import zmq
import json


class HorusComms:
    """
    Only responsibility:
    Horus → Sensei pose streaming
    """

    def __init__(self, pub_addr: str):
        self.ctx = zmq.Context.instance()

        # PUB socket → Sensei
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(pub_addr)

    def publish_pose(self, payload: dict):
        self.pub.send_multipart([
            b"pose.data",
            json.dumps(payload).encode()
        ])