# Network / IPC
ZMQ_ADDR = "tcp://*:5555"
FRAME_INDEX_NAME = "cackle_index"
FRAME_ID_NAME = "cackle_frame_id"

# Buffers
FRONT_PREFIX = "cackle_front_"
SIDE_PREFIX = "cackle_side_"
RING_SIZE = 4

# Hardware Targets (Intent)
# Service will try to set these, but will use actual hardware res for SHM
FRONT_SHAPE = (1080, 1920, 3) 
SIDE_SHAPE = (1080, 1920, 3)
FPS = 30