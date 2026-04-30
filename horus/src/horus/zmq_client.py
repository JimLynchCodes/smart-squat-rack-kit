import zmq


class FrameSubscriber:
    def __init__(self, addr: str):
        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.SUB)
        self.sock.connect(addr)
        self.sock.setsockopt_string(zmq.SUBSCRIBE, "frame.sync")

    def recv(self) -> bytes:
        _, msg = self.sock.recv_multipart()
        return msg