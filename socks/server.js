import zmq from "zeromq";
import { WebSocketServer } from "ws";

const sock = new zmq.Subscriber();
await sock.connect("tcp://127.0.0.1:5557");

sock.subscribe();

const wss = new WebSocketServer({ port: 9000 });

console.log("WebSocket server running on ws://localhost:9000");

const clients = new Set();

wss.on("connection", (ws) => {
  console.log("Frontend connected");

  clients.add(ws);

  ws.on("close", () => {
    clients.delete(ws);
  });
});

for await (const [topic, msg] of sock) {

  const event = topic.toString();
  const payload = JSON.parse(msg.toString());

  const outgoing = JSON.stringify({
    event,
    payload,
  });

  console.log(
    `sending ${outgoing} to ${clients.size} clients`
  );

  for (const client of clients) {
    if (client.readyState === 1) {
      client.send(outgoing);
    }
  }
}