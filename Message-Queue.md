# Message Queue

## Recommended ZeroMQ topology

This is probably the cleanest setup:
```
vision-capture
    └── PUB  → frame.sync

vision-inference
    └── SUB  ← frame.sync
    └── PUB  → motion.events

coach-runtime
    └── SUB  ← motion.events
    └── PUB  → coach.events
    └── REP  ← ui.commands

tablet-app
    └── WS   ↔ coach-runtime
```

That’s a very sane MVP topology.

## Suggested socket patterns
PUB/SUB

Use for:

- pose updates
- rep events
- coaching events

Perfect for:
- one producer → many consumers

Example:

- inference publishes
- coach runtime subscribes
- recorder could subscribe too later

Great fit.

PUSH/PULL

Use for:

- work distribution
- background processing
- analytics jobs

Good for:
- one producer → worker pool

You may want this later for async clip analysis.

REQ/REP

Use for:

- commands
- config
- status checks

Good for:

- start session
- get current config
- health checks

Not ideal for high-frequency streaming.
