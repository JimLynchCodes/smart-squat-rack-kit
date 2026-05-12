import { useEffect, useState, useRef } from "react";

export function useHorus() {
  const [repInfo, setRepInfo] = useState<any>(null);
  const latestPose = useRef<any>(null);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:9000");

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.event === "pose.data") {
          // FIX: Based on Screenshot 2026-05-12 at 5.56.49 PM.png
          // The structure is payload -> pose -> {side, front}
          latestPose.current = msg.payload.pose; 
        } 
        else if (msg.event === "rep.summary") {
          setRepInfo(msg.payload);
        }
      } catch (e) {
        console.error("Parse error", e);
      }
    };

    return () => socket.close();
  }, []);

  return { repInfo, latestPose };
}