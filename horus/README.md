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
