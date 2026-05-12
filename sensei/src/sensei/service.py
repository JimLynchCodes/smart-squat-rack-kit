import json
import time
import zmq

from sensei.config import *
from sensei.set_tracker import SetTracker

# =========================================================
# THE JUDGE: CONFIGURATION
# =========================================================
SCORING_CONFIG = [
    {
        "name": "Depth",
        "weight": 25,
        "min_zero": 0.35, "min_acc": 0.60, "max_acc": 1.20, "max_zero": 1.50
    },
    {
        "name": "Valgus (Knee/Ankle)",
        "weight": 15,
        "min_zero": 0.60, "min_acc": 0.85, "max_acc": 1.30, "max_zero": 1.60
    },
    {
        "name": "Stance (Foot/Shoulder)",
        "weight": 10,
        "min_zero": 0.70, "min_acc": 1.05, "max_acc": 1.45, "max_zero": 1.80
    },
    {
        "name": "Forward Drift (m)",
        "weight": 15,
        "min_zero": -0.20, "min_acc": -0.05, "max_acc": 0.15, "max_zero": 0.30
    },
    {
        "name": "Back Consistency (deg)",
        "weight": 15,
        "min_zero": -5.0,  "min_acc": 0.0,  "max_acc": 15.0, "max_zero": 30.0
    },
    {
        "name": "Torso Angle (deg)",
        "weight": 20,
        "min_zero": -5.0,  "min_acc": 0.0,  "max_acc": 35.0, "max_zero": 60.0
    }
]

def calculate_trapezoid_score(val, cfg):
    """Computes a 0-100 score based on 4-parameter boundaries."""
    if cfg["min_acc"] <= val <= cfg["max_acc"]:
        return 100.0
    if val <= cfg["min_zero"] or val >= cfg["max_zero"]:
        return 0.0
    if cfg["min_zero"] < val < cfg["min_acc"]:
        return ((val - cfg["min_zero"]) / (cfg["min_acc"] - cfg["min_zero"])) * 100.0
    if cfg["max_acc"] < val < cfg["max_zero"]:
        return ((cfg["max_zero"] - val) / (cfg["max_zero"] - cfg["max_acc"])) * 100.0
    return 0.0

def evaluate_rep(metrics):
    total_score = 0.0
    scorecard = []

    # Map Config names to Horus JSON keys
    key_map = {
        "Depth": "lowest_hip_depth",
        "Valgus (Knee/Ankle)": "knee_to_ankle_ratio",
        "Stance (Foot/Shoulder)": "foot_to_shoulder_ratio",
        "Forward Drift (m)": "max_forward_shoulder_drift",
        "Back Consistency (deg)": "back_angle_delta",
        "Torso Angle (deg)": "max_back_angle"
    }

    for check in SCORING_CONFIG:
        metric_key = key_map.get(check["name"])
        val = metrics.get(metric_key, 0.0)
        
        perf_pct = calculate_trapezoid_score(val, check)
        weighted_contribution = (perf_pct / 100.0) * check["weight"]
        total_score += weighted_contribution

        scorecard.append({
            "name": check["name"],
            "performance": round(perf_pct, 1),
            "weight": check["weight"],
            "contribution": round(weighted_contribution, 1),
            "raw_val": round(val, 3)
        })

    return round(total_score), scorecard

# =========================================================
# SERVICE LOOP
# =========================================================
def run():
    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.connect(HORUS_ZMQ_ENDPOINT)
    sub.setsockopt_string(zmq.SUBSCRIBE, "pose.data")
    sub.setsockopt_string(zmq.SUBSCRIBE, "rep.summary")

    pub = ctx.socket(zmq.PUB)
    pub.bind(SENSEI_ZMQ_ADDR)

    set_tracker = SetTracker()
    rep_count = 0
    last_verdict = None

    print(f"[sensei] online | Trapezoidal Engine | Debug Mode: ON")

    try:
        while True:
            topic_bytes, payload = sub.recv_multipart()
            topic = topic_bytes.decode()
            msg = json.loads(payload.decode())

            if topic == "rep.summary":
                rep_count += 1
                
                # --- DEBUG PRINT: RAW HORUS MESSAGE ---
                print(f"\n\033[94m[DEBUG] Incoming Horus Summary (Rep #{rep_count}):\033[0m")
                print(json.dumps(msg, indent=4))
                print("\033[94m" + "="*50 + "\033[0m")

                final_score, scorecard = evaluate_rep(msg)
                
                verdict = {
                    "rep_index": rep_count, 
                    "score": final_score, 
                    "scorecard": scorecard, 
                    "metrics": msg, 
                    "ts": time.time()
                }
                last_verdict = verdict

                # TERMINAL LOGGING (Scorecard View)
                color = "\033[92m" if final_score > 85 else "\033[93m" if final_score > 70 else "\033[91m"
                print(f"{color}SENSEI JUDGMENT: {final_score}/100{0}\033[0m")
                print(f"{'-'*85}")
                print(f"{'CRITERION':<22} | {'RAW':<8} | {'ZERO_M':<8} | {'ACC_M':<8} | {'PERF %':<8} | {'PTS'}")
                print(f"{'-'*85}")
                for s in scorecard:
                    cfg = next(c for c in SCORING_CONFIG if c["name"] == s["name"])
                    p_color = "\033[91m" if s['performance'] < 50 else ""
                    print(f"{s['name']:<22} | {s['raw_val']:<8} | {cfg['min_zero']:<8} | {cfg['min_acc']:<8} | {p_color}{s['performance']:>6}% \033[0m | {s['contribution']}/{s['weight']}")
                print(f"{'-'*85}\n")

                pub.send_multipart([b"rep.summary", json.dumps(verdict).encode()])
                set_tracker.add_rep(verdict)

            elif topic == "pose.data":
                # Regular live flow
                pub.send_multipart([b"ui.live", json.dumps({
                    "ts": time.time(), 
                    "pose": msg.get("pose"), 
                    "rep_count": rep_count, 
                    "last_rep": last_verdict
                }).encode()])

    except KeyboardInterrupt:
        print("\n[sensei] shutting down...")
        set_tracker.finalize()
    finally:
        sub.close()
        pub.close()
        ctx.term()

if __name__ == "__main__":
    run()