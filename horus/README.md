# 🧠 horus

Horus is the inference + coaching brain of the Smart Squat Rack system.

It subscribes to frame streams from `cackle`, reads pixel data from shared memory, and turns movement into structured coaching signals.

---

## 🏗 System architecture

Horus is part of a 2-process vision pipeline:

### 📸 cackle (capture layer)
- captures front + side cameras
- writes frames into shared memory
- publishes `frame.sync` events via ZeroMQ

### 🧠 horus (this repo)
- subscribes to `frame.sync`
- reads pixel frames from shared memory
- runs pose estimation + rep detection
- generates coaching cues

---

## 🔄 Data flow


Horus should send this every frame:

JSON
{
  "frame_id": 1234,
  "pose": { ... }, 
  "instant_metrics": {
     "back_angle": 42.1,
     "knee_angle": 88.5,
     "knee_dist": 0.45,
     "hip_y": 0.72
  },
  "bar_pos": [x, y]
}

```
python -m venv .venv
source .venv/bin/activate
pip install -e .
```


```
{
  "frame_id"       : 125,
  "phase"          : "DESCENT",
  "pose"           : {
    "side" : {
      "keypoints": {
        "left_shoulder" : [0.6159807443618774,  0.3156854510307312],
        "right_shoulder": [0.2249159812927246,  0.2730729877948761],
        "left_elbow"    : [0.7145925760269165,  0.7295022010803223],
        "right_elbow"   : [0.04381193965673447, 0.6751856207847595],
        "left_wrist"    : [0.8074741363525391,  0.8357101678848267],
        "right_wrist"   : [0.09094496071338654, 0.7947542667388916],
        "left_hip"      : [0.5439763069152832,  1.0               ],
        "right_hip"     : [0.306515634059906,   1.0               ],
        "left_knee"     : [0.6340450048446655,  1.0               ],
        "right_knee"    : [0.385672003030777,   0.9498562216758728],
        "left_ankle"    : [0.6690572500228882,  1.0               ],
        "right_ankle"   : [0.5455502271652222,  0.828217089176178 ]
      }
    },
    "front": {"keypoints": {}}
  },
  "instant_metrics": {
    "side" : {
      "back_angle"      :   0.38999998569488525,
      "knee_angle_proxy": 180.0,
      "knee_dist"       :   0.24837300181388855,
      "hip_y"           :   1.0,
      "forearm_angle"   : 148.66000366210938
    },
    "front": {"knee_valgus": 0.0, "stance_width": 0.12350702285766602}
  },
  "bar"            : {
    "position"      : 0.29437921941280365,
    "velocity_y"    : 0.0207,
    "acceleration_y": 0.3216
  },
  "ts"             : 1778365471.831904
}

```