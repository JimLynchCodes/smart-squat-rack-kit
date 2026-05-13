import { useEffect, useState, useRef } from "react";

export function useHorus() {
  const [repInfo, setRepInfo] = useState<any>(null);
  // This ref now holds the full payload (pose, metrics, frame_id, etc.)
  const latestPose = useRef<any>(null);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:9000");

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.event === "pose.data") {
          // Store the WHOLE payload so we don't lose metrics or metadata
          latestPose.current = msg.payload; 
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