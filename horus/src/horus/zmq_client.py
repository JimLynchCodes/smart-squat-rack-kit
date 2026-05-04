import zmq
import json

class HorusComms:
    def __init__(self, sub_addr: str, pub_addr: str):
        self.ctx = zmq.Context.instance()
        
        # Subscriber (Cackle)
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(sub_addr)
        self.sub.setsockopt_string(zmq.SUBSCRIBE, "frame.sync")
        
        # Publisher (Sensei)
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(pub_addr)

    def recv_cackle(self):
        # We use NOBLOCK or poll to ensure we always get the LATEST frame
        try:
            topic, payload = self.sub.recv_multipart(flags=zmq.NOBLOCK)
            return json.loads(payload.decode())
        except zmq.Again:
            return None

    def publish_horus(self, payload: dict):
        self.pub.send_multipart([
            b"pose.data",
            json.dumps(payload).encode()
        ])