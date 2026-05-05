import zmq
import json
import time

from sensei.src.sensei.rep_tracker import RepTracker
from sensei.src.sensei.set_tracker import SetTracker
from sensei.config import *


LOCKOUT_STABILITY_FRAMES = 3
REST_THRESHOLD_SECONDS = 10.0


def run():
    ctx = zmq.Context()

    sub = ctx.socket(zmq.SUB)
    sub.connect(HORUS_ZMQ_ENDPOINT)
    sub.setsockopt_string(zmq.SUBSCRIBE, "pose.data")

    pub = ctx.socket(zmq.PUB)
    pub.bind(SENSEI_ZMQ_ADDR)

    tracker = RepTracker()
    set_tracker = SetTracker(rest_threshold=REST_THRESHOLD_SECONDS)

    current_state = "LOCKOUT"
    lockout_streak = LOCKOUT_STABILITY_FRAMES  # start stable
    rep_pending_completion = False

    print("[sensei] online | state: LOCKOUT | listening...")

    try:
        while True:
            topic, payload = sub.recv_multipart()
            msg = json.loads(payload.decode())

            new_state = msg["rep_phase"]

            # ------------------------------------------------------------
            # LOCKOUT STABILITY TRACKING
            # Require N consecutive LOCKOUT frames before ending a rep.
            # This prevents noisy ASCENT -> LOCKOUT -> ASCENT flicker
            # from double-counting reps.
            # ------------------------------------------------------------
            if new_state == "LOCKOUT":
                lockout_streak += 1
            else:
                lockout_streak = 0

            stable_lockout = lockout_streak >= LOCKOUT_STABILITY_FRAMES

            # ------------------------------------------------------------
            # REP START
            # LOCKOUT -> DESCENT begins a new rep
            # ------------------------------------------------------------
            if current_state == "LOCKOUT" and new_state == "DESCENT":
                print(f"\n[sensei] Rep {msg['frame_id']}: Initiating Descent...")
                tracker.reset()
                tracker.is_active = True
                tracker.start_frame = msg["frame_id"]
                rep_pending_completion = False

            # ------------------------------------------------------------
            # ACTIVE REP TRACKING
            # ------------------------------------------------------------
            if tracker.is_active:
                tracker.update(msg)

            # ------------------------------------------------------------
            # MARK REP AS READY TO COMPLETE
            # Once lifter reaches lockout after ascent, don't finalize yet.
            # Wait until lockout is stable for N frames.
            # ------------------------------------------------------------
            if current_state == "ASCENT" and new_state == "LOCKOUT" and tracker.is_active:
                rep_pending_completion = True

            # ------------------------------------------------------------
            # FINALIZE REP ONLY AFTER STABLE LOCKOUT
            # ------------------------------------------------------------
            if rep_pending_completion and stable_lockout and tracker.is_active:
                summary = tracker.get_summary()

                finished_set = set_tracker.add_rep(summary)

                print(
                    f"[sensei] Rep Validated. "
                    f"Avg Back Angle: {summary['back_angle_average']}°"
                )

                rep_payload = {
                    "event": "REP_COMPLETE",
                    "data": summary,
                    "ts": time.time(),
                }
                pub.send_multipart(
                    [b"rep.summary", json.dumps(rep_payload).encode()]
                )

                if finished_set:
                    set_payload = {
                        "event": "SET_COMPLETE",
                        "data": finished_set,
                        "ts": time.time(),
                    }
                    pub.send_multipart(
                        [b"set.complete", json.dumps(set_payload).encode()]
                    )

                tracker.is_active = False
                rep_pending_completion = False

            current_state = new_state

            # ------------------------------------------------------------
            # LIVE UI PASSTHROUGH
            # ------------------------------------------------------------
            pub.send_multipart([b"ui.live", json.dumps(msg).encode()])

    except KeyboardInterrupt:
        print("\n[sensei] shutting down...")
        set_tracker.finalize()

    finally:
        sub.close()
        pub.close()
        ctx.term()


if __name__ == "__main__":
    run()