import zmq
import json
import time
from sensei.config import *
from sensei.tracker import RepTracker

def run():
    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect(HORUS_ZMQ_ENDPOINT)
    sub.setsockopt_string(zmq.SUBSCRIBE, "pose.data")

    pub = ctx.socket(zmq.PUB)
    pub.bind(SENSEI_ZMQ_ADDR)

    tracker = RepTracker()
    current_state = "LOCKOUT"

    print("[sensei] online | state: LOCKOUT | listening...")

    try:
        while True:
            topic, payload = sub.recv_multipart()
            msg = json.loads(payload.decode())
            
            # The phase coming from Horus (DESCENT, ASCENT, or LOCKOUT)
            new_state = msg['rep_phase']
            
            # --- STATE TRANSITIONS ---
            
            # 1. START: Moving from standing still to dropping down
            if current_state == "LOCKOUT" and new_state == "DESCENT":
                print(f"\n[sensei] Rep {msg['frame_id']}: Initiating Descent...")
                tracker.reset()
                tracker.is_active = True
                tracker.start_frame = msg['frame_id']

            # 2. TRACKING: Feed data to the accumulator while moving
            if tracker.is_active:
                tracker.update(msg)

            # 3. FINISH: Returning to a stable standing position after the ascent
            if current_state == "ASCENT" and new_state == "LOCKOUT" and tracker.is_active:
                summary = tracker.get_summary()
                print(f"[sensei] Rep Validated. Avg Back Angle: {summary['back_angle_average']}°")
                
                # Push results to the UI
                final_payload = {
                    "event": "REP_COMPLETE",
                    "data": summary,
                    "ts": time.time()
                }
                pub.send_multipart([b"rep.summary", json.dumps(final_payload).encode()])
                tracker.is_active = False

            current_state = new_state

            # Optional: Pass-through for live UI rendering
            pub.send_multipart([b"ui.live", json.dumps(msg).encode()])

    except KeyboardInterrupt:
        print("\n[sensei] shutting down...")
    finally:
        sub.close()
        pub.close()

if __name__ == "__main__":
    run()