import React, { useEffect, useRef } from "react";

interface Props {
  message: any;
}

export default function DualPoseViewer({ message }: Props) {
  const frontRef = useRef<HTMLCanvasElement>(null);
  const sideRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!message) return;

    let parsed: any;

    try {
      parsed =
        typeof message.data === "string"
          ? JSON.parse(message.data)
          : message;
    } catch (err) {
      console.error("JSON parse failed:", err);
      return;
    }

    // ================================
    // THIS IS THE REAL DATA SHAPE
    // ================================
    const pose = parsed?.payload?.pose?.pose;

    if (!pose) {
      console.log("NO POSE:", parsed);
      return;
    }

    const front = pose.front;
    const side = pose.side;

    const frontCanvas = frontRef.current;
    const sideCanvas = sideRef.current;

    if (!frontCanvas || !sideCanvas) return;

    const fctx = frontCanvas.getContext("2d");
    const sctx = sideCanvas.getContext("2d");

    if (!fctx || !sctx) return;

    // ================================
    // CLEAR
    // ================================
    fctx.clearRect(0, 0, frontCanvas.width, frontCanvas.height);
    sctx.clearRect(0, 0, sideCanvas.width, sideCanvas.height);

    // ================================
    // GRID
    // ================================
    const drawGrid = (
      ctx: CanvasRenderingContext2D,
      canvas: HTMLCanvasElement
    ) => {
      ctx.strokeStyle = "#151515";

      for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }

      for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }
    };

    drawGrid(fctx, frontCanvas);
    drawGrid(sctx, sideCanvas);

    // ================================
    // DRAW
    // ================================
    const renderPose = (
      ctx: CanvasRenderingContext2D,
      landmarks: Record<string, [number, number]>,
      color: string,
      canvas: HTMLCanvasElement
    ) => {
      Object.entries(landmarks).forEach(([name, point]) => {
        if (!Array.isArray(point)) return;

        const [xNorm, yNorm] = point;

        // skip missing points
        if (xNorm === 0 && yNorm === 0) return;

        const x = xNorm * canvas.width;
        const y = yNorm * canvas.height;

        // glow
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);

        ctx.fillStyle = color;
        ctx.globalAlpha = 0.2;
        ctx.fill();

        // main dot
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);

        ctx.globalAlpha = 1;
        ctx.fillStyle = color;
        ctx.shadowBlur = 20;
        ctx.shadowColor = color;

        ctx.fill();

        ctx.shadowBlur = 0;

        // labels
        ctx.fillStyle = "#fff";
        ctx.font = "10px monospace";
        ctx.fillText(name, x + 8, y - 8);
      });
    };

    if (front) {
      renderPose(
        fctx,
        front,
        "#00d4ff",
        frontCanvas
      );
    }

    if (side) {
      renderPose(
        sctx,
        side,
        "#ff9d00",
        sideCanvas
      );
    }

  }, [message]);

  return (
    <div
      style={{
        display: "flex",
        gap: 24,
        justifyContent: "center",
        background: "#000",
        padding: 20,
      }}
    >
      <div>
        <div
          style={{
            color: "#999",
            textAlign: "center",
            marginBottom: 8,
            fontFamily: "monospace",
            fontSize: 11,
          }}
        >
          SIDE VIEW
        </div>

        <canvas
          ref={sideRef}
          width={320}
          height={520}
          style={{
            background: "#090909",
            borderRadius: 12,
            border: "1px solid #222",
          }}
        />
      </div>

      <div>
        <div
          style={{
            color: "#999",
            textAlign: "center",
            marginBottom: 8,
            fontFamily: "monospace",
            fontSize: 11,
          }}
        >
          FRONT VIEW
        </div>

        <canvas
          ref={frontRef}
          width={320}
          height={520}
          style={{
            background: "#090909",
            borderRadius: 12,
            border: "1px solid #222",
          }}
        />
      </div>
    </div>
  );
}