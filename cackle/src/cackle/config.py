# =========================================================
# CAMERA SELECTION
# =========================================================
# Set these based on your /dev/video* indices
FRONT_CAM_INDEX = 1
SIDE_CAM_INDEX = 0

# Network / IPC
ZMQ_ADDR = "tcp://*:5555"
FRAME_INDEX_NAME = "cackle_frame_index"
FRAME_ID_NAME = "cackle_frame_id"

FRONT_PREFIX = "cackle_front_"
SIDE_PREFIX  = "cackle_side_"

# Buffers
RING_SIZE = 4

# Hardware Targets (Intent)
# Service will try to set these, but will use actual hardware res for SHM
SIDE_SHAPE = (1080, 1920, 3) 
FRONT_SHAPE = (720, 1280, 3)
FPS = 30