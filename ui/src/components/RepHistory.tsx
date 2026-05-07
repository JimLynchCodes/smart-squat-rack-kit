import type { RepSummary } from "../hooks/useSenseiSocket";

interface Props {
  reps: RepSummary[];
}

export default function RepHistory({
  reps,
}: Props) {
  return (
    <div className="card">
      <h2>Training Log</h2>

      <div className="rep-list">
        {reps.map((rep, idx) => (
          <div
            key={idx}
            className="rep-item"
          >
            <div>
              Rep #{reps.length - idx}
            </div>

            <div>
              Lean:{" "}
              {rep.back_angle_steepest_value.toFixed(
                1
              )}
              °
            </div>

            <div>
              Depth:{" "}
              {rep.hip_height_bottom.toFixed(3)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}