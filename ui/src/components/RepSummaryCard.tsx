import type { RepSummary } from "../hooks/useSenseiSocket";

interface Props {
  rep: RepSummary;
}

export default function RepSummaryCard({
  rep,
}: Props) {
  return (
    <div className="card rep-card">
      <h2>Latest Rep</h2>

      <div className="metric">
        <span>Bottom Frame</span>

        <strong>{rep.bottom_frame}</strong>
      </div>

      <div className="metric">
        <span>Average Back Angle</span>

        <strong>
          {rep.back_angle_average.toFixed(1)}°
        </strong>
      </div>

      <div className="metric warning">
        <span>Max Lean</span>

        <strong>
          {rep.back_angle_steepest_value.toFixed(1)}°
        </strong>
      </div>

      <div className="metric">
        <span>Knee Width Max</span>

        <strong>
          {rep.knees_distance_max_value.toFixed(2)}
        </strong>
      </div>
    </div>
  );
}