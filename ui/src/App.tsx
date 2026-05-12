import DualPoseViewer from "./DualPoseViewer";

export default function App() {


  // const message = usePoseSocket("ws://localhost:9000");
  // const data = useHorus();


  return (
    <>
      {/* <HorusDashboard data={data} /> */}

      <DualPoseViewer />
    </>
  );
}