import DualPoseViewer from "./DualPoseViewer";
import HorusDashboard from "./HorusDashboard";
import { useHorus } from "./useHorus";
import { usePoseSocket } from "./usePoseSocket";

export default function App() {


  const message = usePoseSocket("ws://localhost:9000");
  const data = useHorus();


  return (
    <>
      <HorusDashboard data={data} />

      <DualPoseViewer message={message} />
    </>
  );
}