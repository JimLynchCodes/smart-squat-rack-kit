import zmq from "zeromq";
import { WebSocketServer } from "ws";

// ======================================================
// CONFIG
// ======================================================

const HORUS_OUT = "tcp://127.0.0.1:5556";
const SENSEI_OUT = "tcp://127.0.0.1:5557";

const WS_PORT = 9000;

// ======================================================
// WEBSOCKET SERVER
// ======================================================

const wss = new WebSocketServer({
  port: WS_PORT
});

const clients = new Set();

wss.on("connection", (ws) => {
  console.log("🟢 Frontend connected");

  clients.add(ws);

  ws.on("close", () => {
    clients.delete(ws);
    console.log("🔴 Frontend disconnected");
  });
});

console.log(`🚀 WS bridge live on ws://localhost:${WS_PORT}`);

// ======================================================
// BROADCAST HELPER
// ======================================================

function broadcast(event, payload) {

  const outgoing = JSON.stringify({
    event,
    payload
  });

  let activeCount = 0;

  for (const client of clients) {

    if (client.readyState === 1) {

      client.send(outgoing);

      activeCount++;
    }
  }

  return activeCount;
}

// ======================================================
// JSON SANITIZER
// ======================================================

function safeParse(raw) {

  const sanitized = raw
    .replace(/:\s?Infinity/g, ": null")
    .replace(/:\s?-Infinity/g, ": null")
    .replace(/:\s?NaN/g, ": null");

  return JSON.parse(sanitized);
}

// ======================================================
// HORUS STREAM
// ======================================================

async function runHorusBridge() {

  const sock = new zmq.Subscriber();

  console.log(`[HORUS] Connecting -> ${HORUS_OUT}`);

  sock.connect(HORUS_OUT);

  sock.subscribe("");

  for await (const frames of sock) {

    try {

      if (frames.length < 2) {
        console.warn("[HORUS] Invalid frame");
        continue;
      }

      const topic = frames[0].toString();
      const raw = frames[1].toString();

      const payload = safeParse(raw);

      const active = broadcast(topic, payload);

      // Throttle logs
      if (
        payload.frame_id &&
        payload.frame_id % 90 === 0
      ) {
        console.log(
          `📡 [HORUS] frame=${payload.frame_id} -> ${active} clients`
        );
      }

    } catch (err) {

      console.error(
        "[HORUS] Parse Error:",
        err.message
      );
    }
  }
}

// ======================================================
// SENSEI STREAM
// ======================================================

async function runSenseiBridge() {

  const sock = new zmq.Subscriber();

  console.log(`[SENSEI] Connecting -> ${SENSEI_OUT}`);

  sock.connect(SENSEI_OUT);

  sock.subscribe("");

  for await (const frames of sock) {

    try {

      if (frames.length < 2) {
        console.warn("[SENSEI] Invalid frame");
        continue;
      }

      const topic = frames[0].toString();
      const raw = frames[1].toString();

      console.log("🏆 RAW REP MESSAGE:", raw);

      const payload = safeParse(raw);

      const active = broadcast(topic, payload);

      console.log(
        `🏆 [REP] ${topic} -> ${active} clients`
      );

    } catch (err) {

      console.error(
        "[SENSEI] Parse Error:",
        err.message
      );
    }
  }
}

// ======================================================
// MAIN
// ======================================================

async function main() {

  await Promise.all([
    runHorusBridge(),
    runSenseiBridge()
  ]);
}

main().catch(console.error);