"use client";
import { useEffect, useRef, useState } from "react";
import { api, type GraphData } from "@/lib/api";

const FOLDER_COLORS: Record<string, string> = {
  Memoria: "#a78bfa",
  Conversazioni: "#34d399",
  "": "#6c63ff",
};

function folderColor(folder: string): string {
  return FOLDER_COLORS[folder] ?? "#60a5fa";
}

export default function Graph3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<GraphData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getMemoryGraph()
      .then(setData)
      .catch(() => setError("Backend non raggiungibile"));
  }, []);

  useEffect(() => {
    if (!data || !containerRef.current) return;

    let fg: any;
    import("3d-force-graph").then((mod) => {
      if (!containerRef.current) return;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ForceGraph3D = (mod as any).default;

      fg = ForceGraph3D()(containerRef.current)
        .width(containerRef.current.clientWidth)
        .height(containerRef.current.clientHeight)
        .backgroundColor("#0a0a0b")
        .nodeLabel((n: any) => n.name)
        .nodeColor((n: any) => folderColor(n.folder))
        .nodeVal((n: any) => Math.max(1, Math.sqrt(n.size / 50)))
        .nodeOpacity(0.9)
        .linkColor(() => "#2a2a3e")
        .linkOpacity(0.5)
        .linkWidth(0.5)
        .onNodeClick((n: any) => setSelected(n.name))
        .graphData(data);

      fg.d3Force("charge")?.strength(-80);
    });

    return () => { fg?.pauseAnimation?.(); };
  }, [data]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />

      {/* legend */}
      <div
        style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10 }}
        className="absolute top-4 left-4 px-3 py-2 flex flex-col gap-1.5"
      >
        {Object.entries(FOLDER_COLORS).map(([folder, color]) => (
          <div key={folder} className="flex items-center gap-2">
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: color }} />
            <span style={{ color: "var(--muted)", fontSize: 11 }}>{folder || "Root"}</span>
          </div>
        ))}
      </div>

      {/* selected node */}
      {selected && (
        <div
          style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10 }}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2"
        >
          <span style={{ color: "var(--accent2)", fontSize: 13 }}>📄 {selected}</span>
          <button
            onClick={() => setSelected(null)}
            style={{ color: "var(--muted)", marginLeft: 12, fontSize: 11 }}
          >✕</button>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p style={{ color: "var(--muted)" }}>{error}</p>
        </div>
      )}

      {!data && !error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Caricamento grafo...</p>
        </div>
      )}
    </div>
  );
}
