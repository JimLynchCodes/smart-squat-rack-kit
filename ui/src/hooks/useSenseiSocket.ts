import { useEffect, useState } from "react";

export interface PoseMap {
  [key: string]: [number, number];
}

export interface UIUpdateMessage {
  event: "UI_UPDATE";
  frame_id: number;
  pose: PoseMap;
  rep_phase: string;
  instant_metrics: {
    back_angle: number;
    knee_angle_proxy: number;
    hip_y: number;
  };
}

export interface RepSummary {
  bottom_frame: number;
  hip_height_bottom: number;

  back_angle_average: number;

  back_angle_steepest_value: number;
  back_angle_steepest_frame: number;

  back_angle_shallowest_value: number;
  back_angle_shallowest_frame: number;

  knees_distance_average: number;

  knees_distance_max_value: number;
  knees_distance_max_frame: number;
}

export interface RepCompleteMessage {
  event: "REP_COMPLETE";
  data: RepSummary;
  ts: number;
}

type SenseiMessage =
  | UIUpdateMessage
  | RepCompleteMessage;

export function useSenseiSocket() {
  const [liveFrame, setLiveFrame] =
    useState<UIUpdateMessage | null>(null);

  const [repHistory, setRepHistory] =
    useState<RepSummary[]>([]);

  useEffect(() => {
    const socket = new WebSocket(
      "ws://localhost:8080"
    );

    socket.onopen = () => {
      console.log("Connected to Sensei");
    };

    socket.onmessage = (event) => {
      const message: SenseiMessage = JSON.parse(
        event.data
      );

      if (message.event === "UI_UPDATE") {
        setLiveFrame(message);
      }

      if (message.event === "REP_COMPLETE") {
        setRepHistory((prev) => [
          message.data,
          ...prev,
        ]);
      }
    };

    socket.onclose = () => {
      console.log("Disconnected from Sensei");
    };

    return () => {
      socket.close();
    };
  }, []);

  return {
    liveFrame,
    repHistory,
  };
}