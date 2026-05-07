import type { UIUpdateMessage } from "../hooks/useSenseiSocket";

interface Props {
  frame: UIUpdateMessage | null;
}

export default function LiveMetrics({
  frame,
}: Props) {
  if (!frame) {
    return (
      <div className="card">
        Waiting for data...
      </div>
    );
  }

  const metrics = frame.instant_metrics;

  return (
    <div className="card">
      <h2>Live Metrics</h2>

      <div className="metric">
        <span>Phase</span>
        <strong>{frame.rep_phase}</strong>
      </div>

      <div className="metric">
        <span>Back Angle</span>

        <strong>
          {metrics.back_angle.toFixed(1)}°
        </strong>
      </div>

      <div className="metric">
        <span>Knee Angle Proxy</span>

        <strong>
          {metrics.knee_angle_proxy.toFixed(1)}
        </strong>
      </div>

      <div className="metric">
        <span>Hip Height</span>

        <strong>
          {metrics.hip_y.toFixed(3)}
        </strong>
      </div>
    </div>
  );
}