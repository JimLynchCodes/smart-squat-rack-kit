import React, { useEffect, useRef } from "react";
import { useHorus } from "./hooks/useHorus";

export default function DualPoseViewer() {
    const { repInfo, latestPose } = useHorus();
    const frontRef = useRef<HTMLCanvasElement>(null);
    const sideRef = useRef<HTMLCanvasElement>(null);
    const rafRef = useRef<number | null>(null);

    // Restored all original connections
    const CONNECTIONS = [
        ["left_shoulder", "right_shoulder"],
        ["left_shoulder", "left_elbow"],
        ["left_elbow", "left_wrist"],
        ["right_shoulder", "right_elbow"],
        ["right_elbow", "right_wrist"],
        ["left_hip", "right_hip"],
        ["left_hip", "left_knee"],
        ["left_knee", "left_ankle"],
        ["right_hip", "right_knee"],
        ["right_knee", "right_ankle"],
        ["shoulder_midpoint", "hip_midpoint"],
    ];

    const drawPoints = (
        ctx: CanvasRenderingContext2D,
        landmarks: any,
        color: string
    ) => {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        if (!landmarks || typeof landmarks !== "object") return;

        const pts = { ...landmarks };

        // -----------------------------------
        // Add Midpoints
        // -----------------------------------
        const makeMidpoint = (a: string, b: string) => {
            const p1 = landmarks[a];
            const p2 = landmarks[b];
            if (!Array.isArray(p1) || !Array.isArray(p2)) return [0, 0];
            if ((p1[0] === 0 && p1[1] === 0) || (p2[0] === 0 && p2[1] === 0)) return [0, 0];
            return [(p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5];
        };

        pts.shoulder_midpoint = makeMidpoint("left_shoulder", "right_shoulder");
        pts.hip_midpoint = makeMidpoint("left_hip", "right_hip");

        const getPoint = (name: string) => {
            const coords = pts[name];
            if (!Array.isArray(coords) || coords.length < 2) return null;
            const [x, y] = coords;
            if (x === 0 && y === 0) return null;

            return {
                x: x * ctx.canvas.width,
                y: y * ctx.canvas.height,
            };
        };

        // -----------------------------------
        // Draw Bones (Lines)
        // -----------------------------------
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;

        CONNECTIONS.forEach(([a, b]) => {
            const p1 = getPoint(a);
            const p2 = getPoint(b);
            if (!p1 || !p2) return;

            // Optional: Make the spine green specifically
            if (a === "shoulder_midpoint") ctx.strokeStyle = "#00ff00";
            else ctx.strokeStyle = color;

            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        });

        // -----------------------------------
        // Draw Dots + Labels
        // -----------------------------------
        Object.entries(pts).forEach(([part, coords]: [string, any]) => {
            const p = getPoint(part);
            if (!p) return;

            // Set specific colors for eyes and ears
            if (part.includes("eye")) {
                ctx.fillStyle = "#ff00ff"; // Magenta
            } else if (part.includes("ear")) {
                ctx.fillStyle = "#ffffff"; // White
            } else if (part.includes("midpoint")) {
                ctx.fillStyle = "#00ff00"; // Green
            } else {
                ctx.fillStyle = color;     // Original Theme Color
            }

            // Dot
            ctx.beginPath();
            ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
            ctx.fill();

            // Label
            ctx.fillStyle = "white";
            ctx.font = "10px monospace";
            ctx.fillText(part.toUpperCase(), p.x + 8, p.y - 5);
        });
    }

    const loop = () => {
        const poseData = latestPose.current;
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