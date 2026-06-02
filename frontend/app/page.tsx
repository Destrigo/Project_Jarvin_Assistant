import { Bot } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";

export default function Home() {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* topbar */}
      <header
        style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}
        className="flex items-center gap-3 px-4 py-3 shrink-0"
      >
        <div
          style={{ background: "var(--accent)", borderRadius: "8px", padding: "5px" }}
          className="flex items-center justify-center"
        >
          <Bot size={16} color="#fff" />
        </div>
        <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>
          Jarvis
        </span>
        <span style={{ color: "var(--muted)" }} className="text-xs ml-1">
          assistente personale
        </span>
      </header>

      {/* body */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <Chat />
      </div>
    </div>
  );
}
