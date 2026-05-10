import { useEffect, useState } from "react";
import type { LivePoseMessage } from "./types";

export function usePoseSocket(url: string) {
  const [message, setMessage] = useState<LivePoseMessage | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log("WS connected");
    };

    ws.onmessage = (event) => {
      try {
        const msg: LivePoseMessage = JSON.parse(event.data);

        if (msg.event === "ui.live") {
          setMessage(msg);
        }
      } catch (err) {
        console.error("Invalid WS message", err);
      }
    };

    ws.onerror = (err) => console.error("WS error", err);

    return () => ws.close();
  }, [url]);

  return message;
}