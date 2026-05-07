import zmq from "zeromq";
import { WebSocketServer } from "ws";

const sock = new zmq.Subscriber();
await sock.connect("tcp://127.0.0.1:5557");

sock.subscribe();

const wss = new WebSocketServer({ port: 8080 });

console.log("WebSocket server running on ws://localhost:8080");

const clients = new Set();

wss.on("connection", (ws) => {
  console.log("Frontend connected");

  clients.add(ws);

  ws.on("close", () => {
    clients.delete(ws);
  });
});

for await (const [msg] of sock) {
  const payload = msg.toString();

  for (const client of clients) {
    if (client.readyState === 1) {
      client.send(payload);
    }
  }
}