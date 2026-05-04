HORUS_ZMQ_ENDPOINT = "tcp://127.0.0.1:5556"
SENSEI_ZMQ_ADDR = "tcp://*:5557"

# Velocity threshold: If movement is slower than this, you're at LOCKOUT
# Note: YOLO coordinates are 0.0 to 1.0, so 0.01 is 1% of screen height per second.
VELOCITY_THRESHOLD = 0.01