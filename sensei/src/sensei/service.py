import zmq
import json
import time

from sensei.config import *
from sensei.rep_tracker import RepTracker
from sensei.set_tracker import SetTracker


def run():

    ctx = zmq.Context()

    sub = ctx.socket(zmq.SUB)
    sub.connect(HORUS_ZMQ_ENDPOINT)
    sub.setsockopt_string(zmq.SUBSCRIBE, "pose.data")

    pub = ctx.socket(zmq.PUB)
    pub.bind(SENSEI_ZMQ_ADDR)

    tracker = RepTracker()
    set_tracker = SetTracker()

    print("[sensei] online | listening...")

    try:
        while True:

            _, payload = sub.recv_multipart()
            msg = json.loads(payload.decode())

            # ===========================
            # ONLY THIS LINE MATTERS NOW
            # ===========================
            tracker.update(msg)

            # ===========================
            # REP COMPLETE EVENT
            # ===========================
            if tracker.consume_rep_finished():

                summary = tracker.get_summary()
                score = tracker.last_score

                print(
                    f"[sensei] Rep Validated. Avg Back Angle: "
                    f"{summary['back_angle_average']}°"
                )
                print(f"[sensei] Rep Score: {score}/100")

                pub.send_multipart([
                    b"rep.summary",
                    json.dumps({
                        "event": "REP_COMPLETE",
                        "data": summary,
                        "score": score,
                        "ts": time.time()
                    }).encode()
                ])

                set_tracker.add_rep(summary)
                tracker.clear_rep()

            # ===========================
            # LIVE UI
            # ===========================
            pub.send_multipart([
                b"ui.live",
                json.dumps(msg).encode()
            ])

    except KeyboardInterrupt:
        print("\n[sensei] shutting down...")
        set_tracker.finalize()

    finally:
        sub.close()
        pub.close()
        ctx.term()


if __name__ == "__main__":
    run()