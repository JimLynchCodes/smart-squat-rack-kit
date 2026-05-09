"""
Horus Configuration
Shared constants for Cackle → Horus → Sensei pipeline
"""

# =========================================================
# ZMQ (CACKLE → HORUS)
# =========================================================
HORUS_ZMQ_ENDPOINT = "tcp://127.0.0.1:5555"

# =========================================================
# ZMQ (HORUS → SENSEI)
# =========================================================
HORUS_PUB_ADDR = "tcp://127.0.0.1:5556"

# =========================================================
# FRAME METADATA TOPIC
# =========================================================
FRAME_TOPIC = "frame.sync"

# =========================================================
# HORUS OUTPUT TOPIC
# =========================================================
POSE_TOPIC = "pose.data"

# =========================================================
# SHARED MEMORY (CACKLE RING BUFFER)
# =========================================================
RING_SIZE = 64

FRAME_INDEX_NAME = "cackle_frame_index"
FRAME_ID_NAME = "cackle_frame_id"

FRONT_PREFIX = "cackle_front_"
SIDE_PREFIX  = "cackle_side_"

# =========================================================
# CAMERA / PIPELINE DEFAULTS (REFERENCE ONLY)
# =========================================================
FPS = 30

FRONT_SHAPE = (1080, 1920, 3)
SIDE_SHAPE = (720, 1280, 3)

# =========================================================
# HORUS PIPELINE THRESHOLDS
# =========================================================
VEL_THRESHOLD = 0.01
LOCKOUT_STABILITY_FRAMES = 3

# =========================================================
# SENSEI SETTINGS
# =========================================================
REST_THRESHOLD_SECONDS = 10.0