import React, { useEffect, useRef } from "react";
import { drawSkeleton, FRONT_BONES, SIDE_BONES } from "./skeleton";
import type { LivePoseMessage } from "./types";

interface Props {
  message: LivePoseMessage | null;
}

export default function DualPoseViewer({ message }: Props) {
  const frontRef = useRef<HTMLCanvasElement | null>(null);
  const sideRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {

      
      if (!message) return;
      
      console.log("got new message")
      console.log(message)

    const front = message.payload.pose.front;
    const side = message.payload.pose.side;

    const frontCanvas = frontRef.current;
    const sideCanvas = sideRef.current;

    if (!frontCanvas || !sideCanvas) return;

    const fctx = frontCanvas.getContext("2d");
    const sctx = sideCanvas.getContext("2d");

    if (!fctx || !sctx) return;

    fctx.clearRect(0, 0, frontCanvas.width, frontCanvas.height);
    sctx.clearRect(0, 0, sideCanvas.width, sideCanvas.height);

    drawSkeleton(fctx, front, FRONT_BONES, "#00d4ff");
    drawSkeleton(sctx, side, SIDE_BONES, "#ff9d00");
  }, [message]);

  return (
    <div style={{ display: "flex", gap: 24, justifyContent: "center" }}>
      <div>
        <div style={{ color: "#aaa", marginBottom: 6 }}>Side</div>
        <canvas
          ref={sideRef}
          width={320}
          height={520}
          style={{ background: "#111", borderRadius: 12 }}
        />
      </div>

      <div>
        <div style={{ color: "#aaa", marginBottom: 6 }}>Front</div>
        <canvas
          ref={frontRef}
          width={320}
          height={520}
          style={{ background: "#111", borderRadius: 12 }}
        />
      </div>
    </div>
  );
}