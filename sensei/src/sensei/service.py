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

RAW_SCORING_CONFIG = [
    {
        "name": "Squat Depth",
        "weight": 25,

        # Measures hip crease relative to knee top.
        # 0.0 is parallel; > 0.05 is breaking parallel.
        "min_zero": -1.0,
        "min_acc": 0.05,
        "max_acc": 1.0,
        "max_zero": 1.0
    },
    {
        "name": "Valgus (Stability)",
        "weight": 20,

        # Ratio of Min Knee Distance / Avg Knee Distance.
        # Detects knee cave during the rep.
        "min_zero": 0.60,
        "min_acc": 0.85,
        "max_acc": 1.10,
        "max_zero": 1.20
    },
    {
        "name": "Stance Width",
        "weight": 10,

        # Foot Width / Shoulder Width.
        "min_zero": 0.70,
        "min_acc": 1.00,
        "max_acc": 1.50,
        "max_zero": 1.90
    },
    {
        "name": "Forward Drift",
        "weight": 15,

        # Horizontal travel of shoulders relative to ankle/midfoot.
        "min_zero": -0.15,
        "min_acc": -0.05,
        "max_acc": 0.10,
        "max_zero": 0.25
    },
    {
        "name": "Back Consistency",
        "weight": 15,

        # Difference between max/min torso angle.
        # Lower values are better.
        "min_zero": 30.0,
        "min_acc": 15.0,
        "max_acc": 0.0,
        "max_zero": -5.0
    },
    {
        "name": "Torso Lean (Avg)",
        "weight": 15,

        # Average torso angle.
        "min_zero": 65.0,
        "min_acc": 45.0,
        "max_acc": 5.0,
        "max_zero": -5.0
    },
    {
        "name": "Elbow Flare",
        "weight": 10,

        # Lower is better.
        # Degrees away from ideal elbow tracking.

        "min_zero": 45.0,
        "min_acc": 20.0,
        "max_acc": 10.0,
        "max_zero": 0.0
    }
]


# =========================================================
# WEIGHT NORMALIZATION
# =========================================================

def normalize_weights(config):
    """
    Automatically normalize all weights to total 100.
    """

    total = sum(c["weight"] for c in config)

    if total == 0:
        raise ValueError("Total scoring weight cannot be zero.")

    normalized = []

    for c in config:

        copy = dict(c)

        copy["normalized_weight"] = (
            c["weight"] / total
        ) * 100.0

        normalized.append(copy)

    return normalized


SCORING_CONFIG = normalize_weights(RAW_SCORING_CONFIG)

TOTAL_WEIGHT = sum(
    c["normalized_weight"]
    for c in SCORING_CONFIG
)

print(
    f"[sensei] normalized scoring weights => "
    f"{TOTAL_WEIGHT:.2f}"
)


# =========================================================
# SCORING ENGINE
# =========================================================

def calculate_trapezoid_score(val, cfg):
    """
    Computes a 0-100 score based on trapezoidal boundaries.

    Supports:
    - Ascending metrics (higher is better)
    - Descending metrics (lower is better)
    """

    descending = cfg["min_acc"] > cfg["max_acc"]

    # =====================================================
    # DESCENDING METRICS
    # =====================================================

    if descending:

        # Perfect Zone
        if val <= cfg["max_acc"]:
            return 100.0

        # Fully Failed
        if val >= cfg["min_zero"]:
            return 0.0

        # Linear Ramp
        return (
            (cfg["min_zero"] - val)
            / (cfg["min_zero"] - cfg["min_acc"])
        ) * 100.0

    # =====================================================
    # ASCENDING METRICS
    # =====================================================

    # Perfect Zone
    if cfg["min_acc"] <= val <= cfg["max_acc"]:
        return 100.0

    # Fully Failed
    if val <= cfg["min_zero"] or val >= cfg["max_zero"]:
        return 0.0

    # Lower Ramp
    if cfg["min_zero"] < val < cfg["min_acc"]:
        return (
            (val - cfg["min_zero"])
            / (cfg["min_acc"] - cfg["min_zero"])
        ) * 100.0

    # Upper Ramp
    if cfg["max_acc"] < val < cfg["max_zero"]:
        return (
            (cfg["max_zero"] - val)
            / (cfg["max_zero"] - cfg["max_acc"])
        ) * 100.0

    return 0.0


# =========================================================
# REP EVALUATION
# =========================================================

def evaluate_rep(metrics):
    """
    Takes the raw rep summary from Horus and maps it
    to the scoring configuration.

    Returns:
        total_score,
        scorecard,
        debug_payload
    """

    total_score = 0.0
    scorecard = []

    # =====================================================
    # KNEE STABILITY / VALGUS
    # =====================================================

    avg_k = metrics.get("avg_knee_distance", 1.0)
    min_k = metrics.get("min_knee_distance", 1.0)

    valgus_ratio = min_k / max(0.01, avg_k)

    # =====================================================
    # ELBOW FLARE
    # =====================================================

    max_elbow_flare = metrics.get(
        "max_elbow_flare",
        0.0
    )

    min_elbow_flare = metrics.get(
        "min_elbow_flare",
        0.0
    )

    avg_elbow_flare = (
        max_elbow_flare + min_elbow_flare
    ) / 2.0

    elbow_flare_delta = (
        max_elbow_flare - min_elbow_flare
    )

    # =====================================================
    # INTERMEDIATE PAYLOAD
    # =====================================================

    intermediate = {

        # Knee Tracking
        "avg_knee_distance": avg_k,
        "min_knee_distance": min_k,
        "valgus_ratio": valgus_ratio,

        # Elbow Flare
        "max_elbow_flare": max_elbow_flare,
        "min_elbow_flare": min_elbow_flare,
        "avg_elbow_flare": avg_elbow_flare,
        "elbow_flare_delta": elbow_flare_delta,
    }

    # =====================================================
    # MAP RAW METRICS
    # =====================================================

    key_map_values = {
        "Squat Depth":
            metrics.get(
                "hip_knee_depth_ratio",
                0.0
            ),

        "Valgus (Stability)":
            valgus_ratio,

        "Stance Width":
            metrics.get(
                "foot_to_shoulder_ratio",
                0.0
            ),

        "Forward Drift":
            metrics.get(
                "max_forward_shoulder_drift",
                0.0
            ),

        "Back Consistency":
            metrics.get(
                "back_angle_delta",
                0.0
            ),

        "Torso Lean (Avg)":
            metrics.get(
                "avg_back_angle",
                0.0
            ),

        # Score using WORST observed flare
        "Elbow Flare":
            max_elbow_flare,
    }

    # =====================================================
    # SCORE EACH METRIC
    # =====================================================

    for check in SCORING_CONFIG:

        val = key_map_values.get(
            check["name"],
            0.0
        )

        perf_pct = calculate_trapezoid_score(
            val,
            check
        )

        weighted_contribution = (
            (perf_pct / 100.0)
            * check["normalized_weight"]
        )

        total_score += weighted_contribution

        descending = (
            check["min_acc"]
            > check["max_acc"]
        )

        # =================================================
        # DETERMINE REGION
        # =================================================

        region = "unknown"

        if descending:

            if val <= check["max_acc"]:
                region = "optimal"

            elif val >= check["min_zero"]:
                region = "failed"

            else:
                region = "ramp"

        else:

            if (
                check["min_acc"]
                <= val
                <= check["max_acc"]
            ):
                region = "optimal"

            elif (
                val <= check["min_zero"]
                or val >= check["max_zero"]
            ):
                region = "failed"

            elif (
                check["min_zero"]
                < val
                < check["min_acc"]
            ):
                region = "lower_ramp"

            elif (
                check["max_acc"]
                < val
                < check["max_zero"]
            ):
                region = "upper_ramp"

        # =================================================
        # SCORECARD ENTRY
        # =================================================

        score_entry = {

            # Basic Info
            "name": check["name"],

            # Original Weight
            "raw_weight": check["weight"],

            # Final Normalized Weight
            "weight": round(
                check["normalized_weight"],
                4
            ),

            # Raw Measurement Used For Scoring
            "raw_val": round(val, 5),

            # Performance
            "performance": round(
                perf_pct,
                2
            ),

            "contribution": round(
                weighted_contribution,
                4
            ),

            # Scoring Metadata
            "mode":
                "descending"
                if descending
                else "ascending",

            "region": region,

            "passed": perf_pct >= 70.0,

            # Helpful Normalized Value
            "normalized_contribution":
                round(
                    weighted_contribution
                    / check["normalized_weight"],
                    5
                ),

            # Full Trapezoid Definition
            "ranges": {
                "min_zero": check["min_zero"],
                "min_acc": check["min_acc"],
                "max_acc": check["max_acc"],
                "max_zero": check["max_zero"],
            }
        }

        scorecard.append(score_entry)

    # =====================================================
    # DEBUG PAYLOAD
    # =====================================================

    debug_payload = {

        # Intermediate derived values
        "intermediate": intermediate,

        # Final mapped values used for scoring
        "mapped_values": key_map_values,

        # Entire scoring config
        "scoring_config": SCORING_CONFIG,

        # Weight Diagnostics
        "weight_total": TOTAL_WEIGHT
    }

    return (
        round(total_score),
        scorecard,
        debug_payload
    )


# =========================================================
# SERVICE LOOP
# =========================================================

def run():

    ctx = zmq.Context()

    # =====================================================
    # HORUS SUBSCRIBER
    # =====================================================

    sub = ctx.socket(zmq.SUB)

    sub.connect(HORUS_ZMQ_ENDPOINT)

    # Listen only for rep summaries
    sub.setsockopt_string(
        zmq.SUBSCRIBE,
        "rep.summary"
    )

    # =====================================================
    # SENSEI PUBLISHER
    # =====================================================

    pub = ctx.socket(zmq.PUB)

    pub.bind(SENSEI_ZMQ_ADDR)

    rep_count = 0

    print(
        "[sensei] online | "
        "Scoring Engine: Active | "
        "Monitoring Horus..."
    )

    try:

        while True:

            topic_bytes, payload = (
                sub.recv_multipart()
            )

            msg = json.loads(
                payload.decode()
            )

            rep_count += 1

            (
                final_score,
                scorecard,
                debug_payload
            ) = evaluate_rep(msg)

            # =================================================
            # FINAL VERDICT
            # =================================================

            verdict = {
                "rep_index": rep_count,

                "score": final_score,

                "scorecard": scorecard,

                # Original metrics from Horus
                "metrics": msg,

                "metric_ranges": extract_ranges(scorecard),

                # Full debug + intermediate state
                "debug": debug_payload,

                "ts": time.time()
            }

            # =================================================
            # TERMINAL OUTPUT
            # =================================================

            color = (
                "\033[92m"
                if final_score > 85
                else "\033[93m"
                if final_score > 70
                else "\033[91m"
            )

            print(
                f"\n{color}"
                f"--- REP #{rep_count} | "
                f"JUDGMENT: {final_score}/100 --- "
                f"\033[0m"
            )

            print(
                f"{'CRITERION':<24} | "
                f"{'RAW':<10} | "
                f"{'SCORE':<10} | "
                f"{'WEIGHT':<10}"
            )

            print("-" * 85)

            for s in scorecard:

                print(
                    f"{s['name']:<24} | "
                    f"{s['raw_val']:<10} | "
                    f"{s['performance']}%{'':<4} | "
                    f"{s['weight']:<10.2f}"
                )

            # =================================================
            # PUBLISH TO FRONTEND / ECOSYSTEM
            # =================================================

            print(
                f"publishing sensei message"
            )

            pub.send_multipart([
                b"rep.summary",
                json.dumps(verdict).encode()
            ])



    except KeyboardInterrupt:

        print("\n[sensei] shutting down...")

    finally:

        sub.close()
        pub.close()
        ctx.term()

def extract_ranges(scorecard):
    """
    Converts scorecard into frontend-friendly trapezoid map.
    """
    out = {}

    for item in scorecard:
        out[item["name"]] = {
            "value": item["raw_val"],
            "ranges": item["ranges"],
            "direction": item["mode"],
            "region": item["region"]
        }

    return out


if __name__ == "__main__":
    run()
    
