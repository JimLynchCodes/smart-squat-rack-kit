import type { PoseMap } from "../hooks/useSenseiSocket";

interface Props {
  pose?: PoseMap;
}

const CONNECTIONS: [string, string][] = [
  ["left_shoulder", "right_shoulder"],

  ["left_shoulder", "left_hip"],
  ["right_shoulder", "right_hip"],

  ["left_hip", "right_hip"],

  ["left_hip", "left_knee"],
  ["left_knee", "left_ankle"],

  ["right_hip", "right_knee"],
  ["right_knee", "right_ankle"],
];

export default function PoseCanvas({
  pose,
}: Props) {
  const width = 500;
  const height = 500;

  return (
    <svg
      width={width}
      height={height}
      className="pose-canvas"
    >
      {pose &&
        CONNECTIONS.map(([a, b], idx) => {
          const p1 = pose[a];
          const p2 = pose[b];

          if (!p1 || !p2) {
            return null;
          }

          return (
            <line
              key={idx}
              x1={p1[0] * width}
              y1={p1[1] * height}
              x2={p2[0] * width}
              y2={p2[1] * height}
              stroke="lime"
              strokeWidth={4}
            />
          );
        })}

      {pose &&
        Object.entries(pose).map(
          ([name, point]) => (
            <circle
              key={name}
              cx={point[0] * width}
              cy={point[1] * height}
              r={6}
              fill="cyan"
            />
          )
        )}
    </svg>
  );
}