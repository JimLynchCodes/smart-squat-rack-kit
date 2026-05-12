import json
import time
import zmq

from sensei.config import *
from sensei.set_tracker import SetTracker

# =========================================================
# SCORING ENGINE (The Heart of Sensei)
# =========================================================
def calculate_rep_score(summary):
    """
    Evaluates a rep summary and returns a score (1-100) and specific feedback.
    """
    score = 100
    deductions = []

    # 1. Depth Check (The most important factor)
    # Target depth varies by calibration, but higher Y = deeper.
    depth = summary.get("lowest_hip_depth", 0)
    if depth < 0.45:
        penalty = 40
        score -= penalty
        deductions.append(f"Depth too shallow (-{penalty} pts)")
    elif depth < 0.55:
        penalty = 15
        score -= penalty
        deductions.append(f"Borderline depth (-{penalty} pts)")

    # 2. Back Angle / Torso Rigidity
    # Excessive lean (high angle) indicates core collapse or quad weakness.
    max_back = summary.get("max_back_angle", 0)
    if max_back > 50:
        penalty = 30
        score -= penalty
        deductions.append(f"Excessive forward lean (-{penalty} pts)")
    elif max_back > 35:
        penalty = 10
        score -= penalty
        deductions.append(f"Minor torso lean (-{penalty} pts)")

    # 3. Consistency (Avg vs Max Angle)
    # A large gap suggests a "good morning" squat (hips rising too fast).
    avg_back = summary.get("avg_back_angle", 0)
    if (max_back - avg_back) > 15:
        penalty = 10
        score -= penalty
        deductions.append(f"Hips rising too fast / Good Morning squat (-{penalty} pts)")

    return max(1, score), deductions


# =========================================================
# MAIN SERVICE
# =========================================================
def run():
    ctx = zmq.Context()

    # SUBSCRIBE TO HORUS
    sub = ctx.socket(zmq.SUB)
    sub.connect(HORUS_ZMQ_ENDPOINT)
    sub.setsockopt_string(zmq.SUBSCRIBE, "pose.data")
    sub.setsockopt_string(zmq.SUBSCRIBE, "rep.summary")

    # PUBLISH EVENTS/UI
    pub = ctx.socket(zmq.PUB)
    pub.bind(SENSEI_ZMQ_ADDR)

    set_tracker = SetTracker()
    rep_count = 0
    last_rep_summary = None

    print(f"[sensei] online | Scoring Engine active | Target: {SENSEI_ZMQ_ADDR}")

    try:
        while True:
            topic_bytes, payload = sub.recv_multipart()
            topic = topic_bytes.decode()
            
            try:
                msg = json.loads(payload.decode())
            except Exception as e:
                print(f"[sensei] decoding error: {e}")
                continue

            # -----------------------------------------------------
            # CASE: REP COMPLETE (SCORING PHASE)
            # -----------------------------------------------------
            if topic == "rep.summary":
                rep_count += 1
                
                # RUN THE JUDGE
                score, faults = calculate_rep_score(msg)
                
                # Construct the final verdict
                verdict = {
                    "rep_index": rep_count,
                    "score": score,
                    "faults": faults,
                    "metrics": msg, # Includes frame IDs for key moments
                    "ts": time.time()
                }
                last_rep_summary = verdict

                # LOGGING (Beautifully formatted for the terminal)
                color = "\033[92m" if score > 80 else "\033[93m" if score > 60 else "\033[91m"
                reset = "\033[0m"

                print(f"\n{color}REP #{rep_count} COMPLETE | SCORE: {score}/100{reset}")
                print(f"  > Depth: {msg.get('lowest_hip_depth'):.4f}")
                print(f"  > Max Back Angle: {msg.get('max_back_angle'):.1f}°")
                if faults:
                    for f in faults:
                        print(f"  [!] {f}")
                else:
                    print("  [✓] Perfect execution.")
                print("-" * 40)

                # Broadcast to UI
                pub.send_multipart([b"rep.summary", json.dumps(verdict).encode()])
                set_tracker.add_rep(verdict)
                continue

            # -----------------------------------------------------
            # CASE: LIVE UI PASSTHROUGH
            # -----------------------------------------------------
            if topic == "pose.data":
                live_payload = {
                    "ts": time.time(),
                    "pose": msg.get("pose"),
                    "metrics": msg.get("instant_metrics"),
                    "bar": msg.get("bar"),
                    "rep_count": rep_count,
                    "last_rep_summary": last_rep_summary # Keep last score visible on UI
                }

                pub.send_multipart([
                    b"ui.live",
                    json.dumps(live_payload).encode()
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