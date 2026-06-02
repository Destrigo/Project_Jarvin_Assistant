"use client";
import { useState } from "react";
import dynamic from "next/dynamic";
import { ChevronLeft, ChevronRight, GitBranch } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";

const Graph3D = dynamic(() => import("@/components/Graph3D"), { ssr: false });

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [graphOpen, setGraphOpen] = useState(false);

  return (
    <div style={{ display: "flex", flex: 1, overflow: "hidden", height: "100%" }}>

      {/* ── left sidebar (email + calendar) ────────────────────────────────── */}
      <div
        style={{
          width: sidebarOpen ? 240 : 0,
          minWidth: sidebarOpen ? 240 : 0,
          overflow: "hidden",
          transition: "width 0.2s, min-width 0.2s",
          position: "relative",
        }}
      >
        {sidebarOpen && <Sidebar />}
      </div>

      {/* toggle sidebar */}
      <button
        onClick={() => setSidebarOpen((v) => !v)}
        title={sidebarOpen ? "Nascondi overview" : "Mostra overview"}
        style={{
          width: 18, flexShrink: 0,
          background: "var(--surface2)",
          borderRight: "1px solid var(--border)",
          borderLeft: "1px solid var(--border)",
          color: "var(--muted)",
          display: "flex", alignItems: "center", justifyContent: "center",
          cursor: "pointer", border: "none",
          transition: "background 0.15s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "var(--surface2)")}
      >
        {sidebarOpen ? <ChevronLeft size={12} /> : <ChevronRight size={12} />}
      </button>

      {/* ── chat ────────────────────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <Chat />
      </div>

      {/* toggle graph */}
      <button
        onClick={() => setGraphOpen((v) => !v)}
        title={graphOpen ? "Nascondi grafo" : "Mostra grafo memoria"}
        style={{
          width: 18, flexShrink: 0,
          background: graphOpen ? "var(--surface2)" : "var(--surface)",
          borderLeft: "1px solid var(--border)",
          borderRight: "none",
          color: graphOpen ? "var(--accent2)" : "var(--muted)",
          display: "flex", alignItems: "center", justifyContent: "center",
          cursor: "pointer", border: "none",
          transition: "background 0.15s, color 0.15s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = graphOpen ? "var(--surface2)" : "var(--surface)")}
      >
        <GitBranch size={11} />
      </button>

      {/* ── graph panel ─────────────────────────────────────────────────────── */}
      <div
        style={{
          width: graphOpen ? 480 : 0,
          minWidth: graphOpen ? 480 : 0,
          overflow: "hidden",
          transition: "width 0.2s, min-width 0.2s",
          borderLeft: graphOpen ? "1px solid var(--border)" : "none",
        }}
      >
        {graphOpen && (
          <div style={{ width: 480, height: "100%" }}>
            <Graph3D />
          </div>
        )}
      </div>

    </div>
  );
}
