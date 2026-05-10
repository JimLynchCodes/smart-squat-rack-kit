type Vec2 = [number, number];

type PoseMap = Record<string, Vec2>;

type MetricsMap = Record<string, number | string>;

export interface HorusPayload {
  frame_id: number;
  phase: string;
  ts: number;

  bar: {
    position: number;
    velocity_y: number;
    acceleration_y?: number;
  };

  pose: {
    side: PoseMap;
    front: PoseMap;
  };

  instant_metrics: {
    side: MetricsMap;
    front: MetricsMap;
  };
}

interface HorusDashboardProps {
  data: HorusPayload | null;
}

export default function HorusDashboard({ data }: HorusDashboardProps) {
  if (!data) {
    return (
      <div className="min-h-screen bg-black text-green-400 p-6 font-mono">
        Waiting for Horus...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        <Header data={data} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <MetricCard
            title="Phase"
            value={data.phase}
          />

          <MetricCard
            title="Bar Velocity"
            value={Number(data.bar?.velocity_y || 0).toFixed(3)}
          />

          <MetricCard
            title="Bar Position"
            value={Number(data.bar?.position || 0).toFixed(3)}
          />

        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <MetricsPanel
            title="Side Metrics"
            metrics={data.instant_metrics?.side || {}}
          />

          <MetricsPanel
            title="Front Metrics"
            metrics={data.instant_metrics?.front || {}}
          />

        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <PosePanel
            title="Side Pose"
            pose={data.pose?.side || {}}
          />

          <PosePanel
            title="Front Pose"
            pose={data.pose?.front || {}}
          />

        </div>

      </div>
    </div>
  );
}

function Header({ data }: { data: HorusPayload }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-2xl">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">

        <div>
          <div className="text-zinc-400 text-sm uppercase tracking-widest">
            Horus Live Feed
          </div>

          <div className="text-4xl font-bold mt-2">
            Frame #{data.frame_id}
          </div>
        </div>

        <div className="flex gap-3 flex-wrap">

          <Pill>
            Phase: {data.phase}
          </Pill>

          <Pill>
            Timestamp: {Math.floor(data.ts || 0)}
          </Pill>

        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-xl">
      <div className="text-zinc-400 text-sm uppercase tracking-wide">
        {title}
      </div>

      <div className="text-4xl font-bold mt-3">
        {value}
      </div>
    </div>
  );
}

function MetricsPanel({ title, metrics }: { title: string; metrics: MetricsMap }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-xl">
      <div className="text-2xl font-semibold mb-5">
        {title}
      </div>

      <div className="space-y-3">
        {Object.entries(metrics).map(([key, value]) => (
          <MetricRow
            key={key}
            label={formatKey(key)}
            value={value}
          />
        ))}
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: number | string }) {
  const formatted =
    typeof value === "number"
      ? value.toFixed(3)
      : String(value);

  return (
    <div className="flex items-center justify-between bg-zinc-800/50 rounded-2xl px-4 py-3">
      <div className="text-zinc-400">
        {label}
      </div>

      <div className="font-mono text-lg font-semibold">
        {formatted}
      </div>
    </div>
  );
}

function PosePanel({ title, pose }: { title: string; pose: PoseMap }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-xl overflow-hidden">
      <div className="text-2xl font-semibold mb-5">
        {title}
      </div>

      <div className="overflow-auto max-h-[600px]">
        <table className="w-full text-sm font-mono">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-400">
              <th className="text-left py-3">Joint</th>
              <th className="text-left py-3">X</th>
              <th className="text-left py-3">Y</th>
            </tr>
          </thead>

          <tbody>
            {Object.entries(pose).map(([joint, coords]) => {
              if (!Array.isArray(coords)) return null;

              return (
                <tr
                  key={joint}
                  className="border-b border-zinc-800/50"
                >
                  <td className="py-3 pr-4">
                    {formatKey(joint)}
                  </td>

                  <td className="py-3 pr-4">
                    {Number(coords[0] || 0).toFixed(4)}
                  </td>

                  <td className="py-3">
                    {Number(coords[1] || 0).toFixed(4)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-zinc-800 border border-zinc-700 rounded-full px-4 py-2 text-sm font-medium">
      {children}
    </div>
  );
}

function formatKey(key: string) {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
