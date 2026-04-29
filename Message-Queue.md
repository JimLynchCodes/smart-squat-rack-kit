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


<br/>

## Key Insight- ZeroMq Is NOT a Server
ZeroMQ is not a server you “start.” That’s the big mental shift.

Unlike Redis / NATS / Kafka, ZeroMQ is a library, not a broker.

That means:

- no daemon
- no background service
- no brew services start zeromq
- no local broker process to boot

Your app imports ZeroMQ, opens sockets, and becomes the messaging system.

That’s the whole model.

What ZeroMQ actually is–

ZeroMQ (“ØMQ”, “0MQ”, “zmq”) is basically:

a socket library with messaging patterns baked in

You use it like sockets, but nicer:

- PUB/SUB
- REQ/REP
- PUSH/PULL

Instead of:

- raw TCP socket code
- custom framing
- reconnect handling
- message routing

ZeroMQ gives you that behavior in-process as a library.

So there is nothing to “run” first.

Your services create sockets and connect directly to each other.

What happens at runtime

When your services start:

- vision-inference opens a PUB socket
- coach-runtime opens a SUB socket
- they connect over localhost

That’s it.

No broker in the middle.

Example:
```
publisher binds to tcp://127.0.0.1:5555
subscriber connects to tcp://127.0.0.1:5555
```
Now messages flow.

The publisher process is the thing serving messages.

On macOS: what you actually install

You install the library so your code can link against it.

Usually:
```
brew install zeromq
```
That installs libzmq.

That’s the core C library.

Then your app uses a language binding:

Python → pyzmq
Rust → zmq
Node → zeromq

So on mac:

install the native library
install your language binding
run your app

That’s it.

No daemon.

Example (Python)

Install:
```
brew install zeromq
pip install pyzmq
```
Then in code:
```
import zmq

ctx = zmq.Context()

sock = ctx.socket(zmq.PUB)
sock.bind("tcp://127.0.0.1:5555")
```
That process is now publishing.

No separate ZeroMQ service exists.

Example (Rust)

Install native lib:
```
brew install zeromq
```
Then in Cargo:
```
zmq = "0.10"
```
And code:
```
let ctx = zmq::Context::new();
let publisher = ctx.socket(zmq::PUB)?;
publisher.bind("tcp://127.0.0.1:5555")?;
```
That process is now the publisher.

Again: no broker process.


<br/>

## Think in domains

Your event names should map to system concepts, not implementation details.

Good domains for your system:

- frame
- pose
- lift
- rep
- technique
- cue
- set
- session
- ui
- system

These become the top-level vocabulary of the whole product.

That’s what makes logs and subscriptions readable.

- Good examples
- Vision layer

Events from computer vision:

- frame.captured
- pose.updated
- pose.lost
- bar_path.updated
- joint_angle.updated

These describe perception.

Lift detection layer

Events from motion interpretation:

- lift.detected
- lift.changed
- rep.started
- rep.bottomed
- rep.completed
- rep.failed

These describe movement state.

Technique layer

Events from form analysis:

- depth.failed
- valgus.detected
- heel_lift.detected
- torso_collapse.detected
- bar_path.forward

These describe technical issues.

Coaching layer

Events from coaching logic:

- cue.generated
- cue.dismissed
- feedback.summarized
- warning.raised

These describe user-facing coaching decisions.

Session layer

Events from workout state:

- session.started
- set.started
- set.ended
- rest.started
- rest.ended

These describe workout flow.

Name what happened, not what code ran

Bad:

- pose_processor_ran
- analyze_knees
- rep_counter_tick

These describe implementation internals.

Good:

- pose.updated
- valgus.detected
- rep.completed

These describe meaningful system events.

That’s what subscribers care about.

Nobody downstream cares that PoseProcessor::tick() ran.
They care that a rep completed.

Use past tense for events

Events should usually be phrased like something already occurred.

Good:

- rep.started
- rep.completed
- cue.generated

Bad:

- start_rep
- complete_rep
- generate_cue

Those sound like commands.

Events are facts, not instructions.

This is one of the biggest things that keeps event systems readable.

Commands should sound different

Commands are different from events.

Commands are requests:

- session.start
- set.begin
- exercise.change

Events are outcomes:

- session.started
- set.began
- exercise.changed

That distinction is worth preserving.

It keeps your system sane.
