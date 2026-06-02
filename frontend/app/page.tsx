import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";

export default function Home() {
  return (
    <div className="flex flex-1 overflow-hidden">
      <Sidebar />
      <Chat />
    </div>
  );
}
