import json
import time
import zmq

from sensei.config import *
from sensei.rep_tracker import RepTracker
from sensei.set_tracker import SetTracker


def safe_clear_rep(tracker: RepTracker):
    """
    Clears rep state safely even if RepTracker
    does not implement clear_rep().
    """

    # Preferred explicit API
    if hasattr(tracker, "clear_rep"):
        tracker.clear_rep()
        return

    # Common alternative names
    for method_name in [
        "reset",
        "reset_rep",
        "clear",
        "new_rep"
    ]:
        if hasattr(tracker, method_name):
            getattr(tracker, method_name)()
            return

    # Last-resort fallback:
    # reinitialize tracker in-place
    print("[sensei] warning: no clear/reset method found, reinitializing tracker")

    tracker.__dict__.clear()
    tracker.__dict__.update(RepTracker().__dict__)


def run():

    ctx = zmq.Context()

    # =====================================
    # SUBSCRIBE TO HORUS POSE STREAM
    # =====================================
    sub = ctx.socket(zmq.SUB)
    sub.connect(HORUS_ZMQ_ENDPOINT)
    sub.setsockopt_string(zmq.SUBSCRIBE, "pose.data")

    # =====================================
    # PUBLISH EVENTS/UI
    # =====================================
    pub = ctx.socket(zmq.PUB)
    pub.bind(SENSEI_ZMQ_ADDR)

    # =====================================
    # TRACKERS
    # =====================================
    tracker = RepTracker()
    set_tracker = SetTracker()

    rep_count = 0
    last_rep_summary = None

    print("[sensei] online | listening...")

    try:

        while True:

            # =====================================
            # RECEIVE POSE DATA
            # =====================================
            topic, payload = sub.recv_multipart()

            try:
                msg = json.loads(payload.decode())

            except Exception as e:
                print(f"[sensei] invalid payload: {e}")
                continue

            # =====================================
            # UPDATE REP TRACKER
            # =====================================
            try:
                tracker.update(msg)

            except Exception as e:
                print(f"[sensei] tracker.update() failed: {e}")
                continue

            # =====================================
            # REP COMPLETED
            # =====================================
            try:

                if tracker.consume_rep_finished():

                    rep_count += 1

                    # -----------------------------
                    # GET SUMMARY SAFELY
                    # -----------------------------
                    try:
                        summary = tracker.get_summary() or {}

                    except Exception as e:
                        print(f"[sensei] get_summary failed: {e}")
                        summary = {}

                    last_rep_summary = summary

                    # -----------------------------
                    # SCORE
                    # -----------------------------
                    score = getattr(tracker, "last_score", 0)

                    # -----------------------------
                    # READABLE METRICS
                    # -----------------------------
                    back_angle = summary.get(
                        "back_angle_average",
                        "N/A"
                    )

                    depth = summary.get(
                        "depth",
                        "N/A"
                    )

                    tempo = summary.get(
                        "tempo",
                        "N/A"
                    )

                    # -----------------------------
                    # CONSOLE LOGGING
                    # -----------------------------
                    print("\n[sensei] =====================")
                    print(f"[sensei] REP #{rep_count} COMPLETE")
                    print(f"[sensei] Back Angle Avg: {back_angle}")
                    print(f"[sensei] Depth: {depth}")
                    print(f"[sensei] Tempo: {tempo}")
                    print(f"[sensei] Score: {score}/100")
                    print("[sensei] =====================\n")

                    # -----------------------------
                    # PUBLISH REP SUMMARY EVENT
                    # -----------------------------
                    event_payload = {
                        "event": "REP_COMPLETE",
                        "rep_index": rep_count,
                        "score": score,
                        "data": summary,
                        "ts": time.time()
                    }

                    pub.send_multipart([
                        b"rep.summary",
                        json.dumps(event_payload).encode()
                    ])

                    # -----------------------------
                    # ADD TO SET TRACKER
                    # -----------------------------
                    try:
                        set_tracker.add_rep(summary)

                    except Exception as e:
                        print(f"[sensei] set_tracker.add_rep failed: {e}")

                    # -----------------------------
                    # CLEAR CURRENT REP STATE
                    # -----------------------------
                    safe_clear_rep(tracker)

            except Exception as e:
                print(f"[sensei] rep completion handling failed: {e}")

            # =====================================
            # LIVE UI STREAM
            # =====================================
            try:

                live_payload = {
                    "ts": time.time(),
                    "pose": msg,
                    "rep_count": rep_count,
                    "last_rep_summary": last_rep_summary
                }

                pub.send_multipart([
                    b"ui.live",
                    json.dumps(live_payload).encode()
                ])

            except Exception as e:
                print(f"[sensei] ui.live publish failed: {e}")

    except KeyboardInterrupt:

        print("\n[sensei] shutting down...")

        try:
            set_tracker.finalize()

        except Exception as e:
            print(f"[sensei] set finalize failed: {e}")

    finally:

        sub.close()
        pub.close()
        ctx.term()

        print("[sensei] offline")


if __name__ == "__main__":
    run()