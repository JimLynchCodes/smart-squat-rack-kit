export const SIDE_BONES: [string, string][] = [
  ["left_hip", "right_hip"],
  ["left_hip", "left_knee"],
  ["right_hip", "right_knee"],
  ["left_knee", "left_ankle"],
  ["right_knee", "right_ankle"],
];

export const FRONT_BONES: [string, string][] = [
  ["left_knee", "right_knee"],
  ["left_knee", "left_ankle"],
  ["right_knee", "right_ankle"],
];

function toPoint(p: [number, number], w: number, h: number) {
  return {
    x: p[0] * w,
    y: (1 - p[1]) * h,
  };
}

export function drawSkeleton(
  ctx: CanvasRenderingContext2D,
  pose: Record<string, [number, number]>,
  bones: [string, string][],
  color: string
) {
  const w = ctx.canvas.width;
  const h = ctx.canvas.height;

  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2;

  for (const [a, b] of bones) {
    const pa = pose[a];
    const pb = pose[b];

    if (!pa || !pb) continue;

    const A = toPoint(pa, w, h);
    const B = toPoint(pb, w, h);

    // bone
    ctx.beginPath();
    ctx.moveTo(A.x, A.y);
    ctx.lineTo(B.x, B.y);
    ctx.stroke();

    // joints
    ctx.beginPath();
    ctx.arc(A.x, A.y, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(B.x, B.y, 4, 0, Math.PI * 2);
    ctx.fill();
  }
}