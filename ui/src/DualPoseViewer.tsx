import React, { useEffect, useRef } from "react";
import { useHorus } from "./hooks/useHorus";

export default function DualPoseViewer() {
  const { repInfo, latestPose } = useHorus();
  const frontRef = useRef<HTMLCanvasElement>(null);
  const sideRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number | null>(null);

  const drawPoints = (ctx: CanvasRenderingContext2D, landmarks: any, color: string) => {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    
    if (!landmarks || typeof landmarks !== 'object') return;

    Object.entries(landmarks).forEach(([part, coords]: [string, any]) => {
      // Coordinates are [x, y] from 0 to 1
      if (!Array.isArray(coords) || coords.length < 2) return;
      
      const [x, y] = coords;
      const px = x * ctx.canvas.width;
      const py = y * ctx.canvas.height;

      // Draw the Dot
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fill();

      // Label
      ctx.fillStyle = "white";
      ctx.font = "10px monospace";
      ctx.fillText(part.toUpperCase(), px + 8, py - 5);
    });
  };

  const loop = () => {
    const poseData = latestPose.current; // This is the payload.pose object
    
    if (poseData) {
      if (frontRef.current && poseData.front) {
        drawPoints(frontRef.current.getContext("2d")!, poseData.front, "#00d4ff");
      }
      if (sideRef.current && poseData.side) {
        drawPoints(sideRef.current.getContext("2d")!, poseData.side, "#ff9d00");
      }
    }
    rafRef.current = requestAnimationFrame(loop);
  };

  useEffect(() => {
    rafRef.current = requestAnimationFrame(loop);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, []);

  return (
    <div style={{ background: "#000", minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", padding: "20px" }}>
      <div style={{ color: "#444", marginBottom: "10px", fontFamily: "monospace" }}>HORUS LIVE STREAM</div>
      
      {repInfo && (
        <div style={{ color: "#0f0", fontSize: "24px", marginBottom: "20px", border: "2px solid #0f0", padding: "10px 20px" }}>
          REP: {repInfo.rep_index} | SCORE: {repInfo.score}%
        </div>
      )}

      <div style={{ display: "flex", gap: "20px" }}>
        <div>
          <div style={{ color: "#ff9d00", textAlign: "center", fontSize: "12px" }}>SIDE</div>
          <canvas ref={sideRef} width={400} height={600} style={{ border: "1px solid #333" }} />
        </div>
        <div>
          <div style={{ color: "#00d4ff", textAlign: "center", fontSize: "12px" }}>FRONT</div>
          <canvas ref={frontRef} width={400} height={600} style={{ border: "1px solid #333" }} />
        </div>
      </div>
    </div>
  );
}