import { useEffect, useState } from "react";

export interface HorusPayload {
  frame_id: number;
  phase: string;
  ts: number;

  bar: {
    position: number;
    velocity_y: number;
    acceleration_y?: number;
  };

  pose: {
    side: Record<string, [number, number]>;
    front: Record<string, [number, number]>;
  };

  instant_metrics: {
    side: Record<string, number | string>;
    front: Record<string, number | string>;
  };
}

export function useHorus() {

  const [data, setData] = useState<HorusPayload | null>(null);

  useEffect(() => {

    const socket = new WebSocket("ws://localhost:9000");

    socket.onopen = () => {
      console.log("[horus] websocket connected");
    };

    socket.onclose = () => {
      console.log("[horus] websocket disconnected");
    };

    socket.onerror = (err) => {
      console.error("[horus] websocket error", err);
    };

    socket.onmessage = (event) => {

      console.log("got new event")
      console.log(event)

      try {

        const msg = JSON.parse(event.data);

        // expected bridge shape:
        // {
        //   event: "ui.live",
        //   payload: {...}
        // }

        if (msg.event !== "ui.live") {
          return;
        }

        setData(msg.payload as HorusPayload);

      } catch (err) {
        console.error("[horus] failed parsing payload", err);
      }
    };

    return () => {
      socket.close();
    };

  }, []);

  return data;
}