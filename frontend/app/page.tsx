import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";

export default function Home() {
  return (
    <div style={{ display: "flex", flex: 1, overflow: "hidden", height: "100%" }}>
      <Sidebar />
      <Chat />
    </div>
  );
}
