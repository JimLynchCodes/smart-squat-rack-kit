import zmq from "zeromq";
import { WebSocketServer } from "ws";

// --- Config ---
const HORUS_OUT = "tcp://127.0.0.1:5556";  // Live Pose Data
const SENSEI_OUT = "tcp://127.0.0.1:5557"; // Rep Summaries
const WS_PORT = 9000;

async function runBridge() {
  const sock = new zmq.Subscriber();

  // Connect to your Python publishers
  console.log(`[ZMQ] Connecting to Horus (${HORUS_OUT}) and Sensei (${SENSEI_OUT})...`);
  await sock.connect(HORUS_OUT);
  await sock.connect(SENSEI_OUT);

  // Subscribe to all topics (no filter)
  sock.subscribe("");

  const wss = new WebSocketServer({ port: WS_PORT });
  const clients = new Set();

  wss.on("connection", (ws) => {
    console.log("🟢 Frontend client linked");
    clients.add(ws);
    ws.on("close", () => clients.delete(ws));
  });

  console.log(`🚀 Bridge live on ws://localhost:${WS_PORT}`);

  // Main Loop
  for await (const [topic, msg] of sock) {
    const topicStr = topic.toString();
    const rawBody = msg.toString();

    try {
      /**
       * CRITICAL: Python's 'json.dumps' can output 'Infinity' or 'NaN' 
       * literals which are NOT valid JSON in JavaScript. 
       * This regex prevents the bridge from crashing.
       */
      const sanitized = rawBody
        .replace(/:\s?Infinity/g, ": null")
        .replace(/:\s?-Infinity/g, ": null")
        .replace(/:\s?NaN/g, ": null");

      const payload = JSON.parse(sanitized);

      // Package for the React Hook
      const outgoing = JSON.stringify({
        event: topicStr,
        payload: payload
      });

      // Broadcast to all active browsers
      let activeCount = 0;
      for (const client of clients) {
        if (client.readyState === 1) { // 1 = OPEN
          client.send(outgoing);
          activeCount++;
        }
      }

      // Logging (throttle pose logs to keep terminal clean)
      if (topicStr === "rep.summary") {
        console.log(`🏆 [REP] Forwarded summary to ${activeCount} clients`);
      } else if (payload.frame_id && payload.frame_id % 90 === 0) {
        console.log(`📡 [POSE] Streaming frame ${payload.frame_id}...`);
      }

    } catch (err) {
      console.error(`⚠️ Error parsing topic [${topicStr}]:`, err.message);
    }
  }
}

runBridge().catch(console.error);