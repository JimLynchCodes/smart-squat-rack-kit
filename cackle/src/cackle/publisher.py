import json
import zmq


class Publisher:
    def __init__(self, addr: str):
        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.PUB)
        self.sock.bind(addr)

    def publish(self, topic: str, payload: dict) -> None:

        print(f"[publishing...] topic: {topic} | paylod: {payload}")

        self.sock.send_multipart(
            [topic.encode("utf-8"), json.dumps(payload).encode("utf-8")]
        )

    def close(self) -> None:
        self.sock.close()