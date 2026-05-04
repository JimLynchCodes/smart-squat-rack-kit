CACKLE_ZMQ_ENDPOINT = "tcp://localhost:5555"
HORUS_ZMQ_ADDR = "tcp://*:5556"
FRONT_PREFIX = "cackle_front_"
SIDE_PREFIX = "cackle_side_"
RING_SIZE = 4

# Model Config
# Using yolov8n-pose.pt for < 30ms latency. 
# Use yolov8s-pose.pt if you need more precision and have a beefy GPU.
YOLO_MODEL_NAME = "yolov8n-pose.pt" 
YOLO_CONFIDENCE = 0.5

# Hardware shapes (Used only as fallbacks now, since service is dynamic)
FRONT_SHAPE = (1080, 1920, 3)
SIDE_SHAPE = (720, 1280, 3)