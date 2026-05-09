import json


def publish_pose(pub, payload):
    pub.send_multipart([
        b"pose.data",
        json.dumps(payload).encode()
    ])