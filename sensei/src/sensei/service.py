import json
import time
import zmq

# Assuming these are defined in your local sensei.config
# If not, you can replace them with your actual strings/ports
try:
    from sensei.config import HORUS_ZMQ_ENDPOINT, SENSEI_ZMQ_ADDR
except ImportError:
    HORUS_ZMQ_ENDPOINT = "tcp://127.0.0.1:5555"
    SENSEI_ZMQ_ADDR = "tcp://127.0.0.1:5556"

# =========================================================
# THE JUDGE: CONFIGURATION
# =========================================================
SCORING_CONFIG = [
    {
        "name": "Squat Depth",
        "weight": 25,
        # Measures hip crease relative to knee top. 
        # 0.0 is parallel; > 0.05 is "breaking parallel" (standard competition depth).
        "min_zero": -1.0, "min_acc": 0.05, "max_acc": 1.0, "max_zero": 1.0
    },
    {
        "name": "Valgus (Stability)",
        "weight": 20,
        # Ratio of Min Knee Distance / Avg Knee Distance.
        # Detects if knees cave inward (valgus) under load relative to the rep average.
        "min_zero": 0.60, "min_acc": 0.85, "max_acc": 1.10, "max_zero": 1.20
    },
    {
        "name": "Stance Width",
        "weight": 10,
        # Foot Width / Shoulder Width. 
        # Ensures a stable base that isn't too narrow or excessively wide for the frame.
        "min_zero": 0.70, "min_acc": 1.00, "max_acc": 1.50, "max_zero": 1.90
    },
    {
        "name": "Forward Drift",
        "weight": 15,
        # Horizontal travel of the shoulders relative to the midfoot/ankle.
        # Excessive drift indicates the center of mass shifting too far forward.
        "min_zero": -0.15, "min_acc": -0.05, "max_acc": 0.10, "max_zero": 0.25
    },
    {
        "name": "Back Consistency",
        "weight": 15,
        # Difference between max and min torso angle.
        # High delta indicates a "good morning squat" where hips rise faster than shoulders.
        "min_zero": 30.0, "min_acc": 15.0, "max_acc": 0.0, "max_zero": -5.0
    },
    {
        "name": "Torso Lean (Avg)",
        "weight": 15,
        # Checks that the overall average torso angle is not too steep (fully upright)
        # or too shallow (folded over) for a standard back squat.
        "min_zero": 65.0, "min_acc": 45.0, "max_acc": 5.0, "max_zero": -5.0
    }
]

# =========================================================
# SCORING ENGINE
# =========================================================
def calculate_trapezoid_score(val, cfg):
    """Computes a 0-100 score based on 4-parameter boundaries."""
    # Special case: If min_acc > max_acc, we are "descending" 
    # (lower raw values are better, e.g., Back Consistency delta)
    if cfg["min_acc"] > cfg["max_acc"]:
        if val <= cfg["max_acc"]: return 100.0
        if val >= cfg["min_zero"]: return 0.0
        # Inverted ramp
        return ((cfg["min_zero"] - val) / (cfg["min_zero"] - cfg["min_acc"])) * 100.0

    # Standard "Ascending" Ramp (higher values are better until max_acc)
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
    """
    Takes the raw rep summary from Horus and maps it to the 
    scoring configuration to produce a final judgment.
    """
    total_score = 0.0
    scorecard = []

    # Valgus stability logic: how much did the knees narrow compared to the average?
    avg_k = metrics.get("avg_knee_distance", 1.0)
    min_k = metrics.get("min_knee_distance", 1.0)
    valgus_ratio = min_k / max(0.01, avg_k)

    # Map the metrics from Horus to our Scored Criteria
    key_map_values = {
        "Squat Depth": metrics.get("hip_knee_depth_ratio", 0.0),
        "Valgus (Stability)": valgus_ratio,
        "Stance Width": metrics.get("foot_to_shoulder_ratio", 0.0),
        "Forward Drift": metrics.get("max_forward_shoulder_drift", 0.0),
        "Back Consistency": metrics.get("back_angle_delta", 0.0),
        "Torso Lean (Avg)": metrics.get("avg_back_angle", 0.0)
    }

    for check in SCORING_CONFIG:
        val = key_map_values.get(check["name"], 0.0)
        
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
    # We specifically want the summaries to judge them
    sub.setsockopt_string(zmq.SUBSCRIBE, "rep.summary")

    pub = ctx.socket(zmq.PUB)
    pub.bind(SENSEI_ZMQ_ADDR)

    rep_count = 0

    print(f"[sensei] online | Scoring Engine: Active | Monitoring Horus...")

    try:
        while True:
            topic_bytes, payload = sub.recv_multipart()
            msg = json.loads(payload.decode())

            rep_count += 1
            final_score, scorecard = evaluate_rep(msg)
            
            # Construct the final verdict
            verdict = {
                "rep_index": rep_count, 
                "score": final_score, 
                "scorecard": scorecard, 
                "metrics": msg, 
                "ts": time.time()
            }

            # Terminal Output for Real-time Feedback
            color = "\033[92m" if final_score > 85 else "\033[93m" if final_score > 70 else "\033[91m"
            print(f"\n{color}--- REP #{rep_count} | JUDGMENT: {final_score}/100 --- \033[0m")
            print(f"{'CRITERION':<20} | {'RAW':<8} | {'SCORE':<8}")
            print("-" * 40)
            for s in scorecard:
                print(f"{s['name']:<20} | {s['raw_val']:<8} | {s['performance']}%")
            
            # Publish verdict to the rest of the ecosystem (UI, Logs, etc.)
            pub.send_multipart([b"rep.summary", json.dumps(verdict).encode()])

    except KeyboardInterrupt:
        print("\n[sensei] shutting down...")
    finally:
        sub.close()
        pub.close()
        ctx.term()

if __name__ == "__main__":
    run()