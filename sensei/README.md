# Sensei


The output of Sensei is the "Final Intelligence" of the system. While Horus outputs raw, frame-by-frame snapshots, Sensei outputs Events and Summaries.When you are squatting, Sensei's ZMQ socket (tcp://*:5557) publishes two types of JSON messages: a Live Stream for your UI and a Rep Summary for your training log.1. The Rep Summary (The "Big Event")This is published only once per rep, the moment you return to the LOCKOUT position. It contains the aggregated "Scorecard" of the movement.JSON{
  "event": "REP_COMPLETE",
  "data": {
    "bottom_frame": 162,
    "hip_height_bottom": 0.824, 
    "back_angle_average": 42.5,
    "back_angle_steepest_value": 56.2,
    "back_angle_steepest_frame": 158,
    "back_angle_shallowest_value": 38.1,
    "back_angle_shallowest_frame": 185,
    "knees_distance_average": 0.28,
    "knees_distance_max_value": 0.31,
    "knees_distance_max_frame": 160
  },
  "ts": 1777580804.55
}
2. The Live UI PassthroughSensei also "forwards" the data from Horus to the frontend. This allows your UI to draw the skeleton on the screen in real-time without having to connect to both services.JSON{
  "event": "UI_UPDATE",
  "frame_id": 805,
  "pose": { "left_hip": [0.52, 0.61], ... },
  "rep_phase": "ASCENT",
  "instant_metrics": {
    "back_angle": 44.2,
    "knee_angle_proxy": 110.5,
    "hip_y": 0.75
  }
}
📊 How the Logic FlowsTo understand why Sensei outputs these specific values, it helps to look at how it maps the "lifecycle" of a squat. It uses the velocity from Horus to move between states:PhaseSensei Internal LogicSensei Output ActionLOCKOUTVelocity < ThresholdPublishes UI_UPDATE; waits for descent.DESCENTVelocity > Threshold (Down)Starts the Rep Timer and begins recording min/max.ASCENTVelocity > Threshold (Up)Continues tracking; looks for the bottom_frame.LOCKOUT (Again)Velocity < ThresholdTriggers REP_COMPLETE; resets the tracker.💡 Why this output is usefulForm Correction: If back_angle_steepest_value is too high, Sensei can trigger an audio alert: "Watch your back lean."Depth Validation: If hip_height_bottom is higher than your recorded knee height, Sensei can log the rep as "No Rep" (red light).Video Review: Because Sensei gives you the bottom_frame, your mobile app can automatically generate a "Highlight Reel" of just the deepest part of every rep you did that day.Essentially, Sensei's output is the Digital Coach talking to your database. Does this data structure cover everything you wanted for your "Sensei" analysis?

## Dev Setup (Mac)

```
python3 -m venv .venv
source .venv/bin/activate
pip install
```