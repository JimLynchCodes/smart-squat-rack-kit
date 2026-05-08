import PoseCanvas from "./components/PoseCanvas";
import LiveMetrics from "./components/LiveMetrics";
import RepSummaryCard from "./components/RepSummaryCard";
import RepHistory from "./components/RepHistory";

import { useSenseiSocket } from "./hooks/useSenseiSocket";

export default function App() {
  const { liveFrame, repHistory } =
    useSenseiSocket();

  const latestRep = repHistory[0];

  return (
    <div className="app">
      <div className="topbar">
        <h1>Sensei Dashboard</h1>

        <div className="status">
          {liveFrame
            ? "LIVE"
            : "DISCONNECTED"}
        </div>
      </div>

      <div className="layout">
        <div className="left-panel">
          <PoseCanvas
            pose={liveFrame?.pose}
          />
        </div>

        <div className="right-panel">
          <LiveMetrics frame={liveFrame} />

          {latestRep && (
            <RepSummaryCard rep={latestRep} />
          )}

          <RepHistory reps={repHistory} />
        </div>
      </div>
    </div>
  );
}