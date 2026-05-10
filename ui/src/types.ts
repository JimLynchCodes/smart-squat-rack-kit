export type Joint = [number, number];

export type PoseSide = Record<string, Joint>;
export type PoseFront = Record<string, Joint>;

export interface LivePoseMessage {
  event: "ui.live";
  payload: {
    frame_id: number;
    phase: string;
    pose: {
      front: PoseFront;
      side: PoseSide;
    };
    instant_metrics?: any;
    bar?: any;
    ts: number;
  };
}