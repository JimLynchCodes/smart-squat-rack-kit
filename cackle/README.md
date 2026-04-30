# cackle


Dual webcam capture service for the AI lifting coach.


## Features


- Front + side webcam capture
- Timestamped frames
- ZeroMQ frame metadata publishing
- Designed for local inference pipeline


## Install


```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```


## Run


```bash
cackle
```


## Output


Publishes to ZeroMQ but also prints to the console some output like this:


```
[publishing...] topic: frame.sync | payload: {'frame_id': 33, 'timestamp_sync': 1777564609.741476, 'active_buffer': 1, 'front': {'camera': 'front', 'frame_id': 33, 'shm': 'cackle_front_1', 'timestamp': 1777564609.76815}, 'side': {'camera': 'side', 'frame_id': 33, 'shm': 'cackle_side_1', 'timestamp': 1777564609.7948842}}
```
