"use client";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { X, FileText } from "lucide-react";
import { api, type GraphData } from "@/lib/api";

const FOLDER_COLORS: Record<string, string> = {
  Memoria: "#a78bfa",
  Conversazioni: "#34d399",
  "": "#6c63ff",
};
function folderColor(f: string) { return FOLDER_COLORS[f] ?? "#60a5fa"; }

type NotePanel = { title: string; content: string; folder: string } | null;

export default function Graph3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<GraphData | null>(null);
  const [note, setNote] = useState<NotePanel>(null);
  const [loadingNote, setLoadingNote] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref so the graph callback always sees the latest version without stale closure
  const openNoteRef = useRef<(name: string) => void>(() => {});

  useEffect(() => {
    openNoteRef.current = async (name: string) => {
      setLoadingNote(true);
      setNote(null);
      try {
        const n = await api.getNote(name);
        setNote({ title: n.title, content: n.content, folder: n.folder });
      } catch {
        setNote({ title: name, content: "*Nota non trovata.*", folder: "" });
      } finally {
        setLoadingNote(false);
      }
    };
  });

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
        .onNodeClick((n: any) => openNoteRef.current(n.name))
        .graphData(data);
      fg.d3Force("charge")?.strength(-80);
    });
    return () => { fg?.pauseAnimation?.(); };
  }, [data]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", display: "flex" }}>
      {/* 3D canvas */}
      <div ref={containerRef} style={{ flex: 1, height: "100%" }} />

      {/* legend */}
      <div style={{ position: "absolute", top: 12, left: 12, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, padding: "8px 12px", display: "flex", flexDirection: "column", gap: 5 }}>
        {Object.entries(FOLDER_COLORS).map(([folder, color]) => (
          <div key={folder} style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
            <span style={{ color: "var(--muted)", fontSize: 11 }}>{folder || "Root"}</span>
          </div>
        ))}
      </div>

      {/* note panel */}
      {(note || loadingNote) && (
        <div
          style={{
            position: "absolute", top: 0, right: 0, bottom: 0,
            width: 320,
            background: "var(--surface)",
            borderLeft: "1px solid var(--border)",
            display: "flex", flexDirection: "column",
            zIndex: 10,
          }}
        >
          {/* header */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 14px", borderBottom: "1px solid var(--border)", flexShrink: 0 }}>
            <FileText size={14} color="var(--accent2)" />
            <span style={{ color: "var(--text)", fontSize: 13, fontWeight: 600, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {loadingNote ? "Caricamento..." : note?.title}
            </span>
            {note?.folder && (
              <span style={{ fontSize: 10, color: "var(--muted)", background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: 4, padding: "1px 6px", flexShrink: 0 }}>
                {note.folder}
              </span>
            )}
            <button onClick={() => setNote(null)} style={{ color: "var(--muted)", flexShrink: 0, background: "none", border: "none", cursor: "pointer", padding: 2 }}>
              <X size={14} />
            </button>
          </div>

          {/* content */}
          <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px" }}>
            {loadingNote ? (
              <p style={{ color: "var(--muted)", fontSize: 13 }}>Caricamento...</p>
            ) : (
              <ReactMarkdown
                components={{
                  h1: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 700, fontSize: 14, margin: "8px 0 4px" }}>{children}</p>,
                  h2: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 600, fontSize: 13, margin: "6px 0 3px" }}>{children}</p>,
                  h3: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 600, fontSize: 12.5, margin: "5px 0 2px" }}>{children}</p>,
                  p: ({ children }) => <p style={{ color: "var(--text)", fontSize: 12.5, lineHeight: 1.65, marginBottom: 6 }}>{children}</p>,
                  strong: ({ children }) => <strong style={{ color: "var(--accent2)" }}>{children}</strong>,
                  em: ({ children }) => <em style={{ color: "var(--muted)" }}>{children}</em>,
                  ul: ({ children }) => <ul style={{ paddingLeft: 14, marginBottom: 6 }}>{children}</ul>,
                  li: ({ children }) => <li style={{ color: "var(--text)", fontSize: 12.5, lineHeight: 1.6, marginBottom: 2 }}>{children}</li>,
                  hr: () => <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "8px 0" }} />,
                  code: ({ children }) => <code style={{ background: "rgba(0,0,0,0.3)", borderRadius: 3, padding: "1px 5px", fontSize: 11, color: "#34d399" }}>{children}</code>,
                }}
              >
                {note?.content ?? ""}
              </ReactMarkdown>
            )}
          </div>
        </div>
      )}

      {error && (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <p style={{ color: "var(--muted)" }}>{error}</p>
        </div>
      )}
      {!data && !error && (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <p style={{ color: "var(--muted)", fontSize: 13 }}>Caricamento grafo memoria...</p>
        </div>
      )}
    </div>
  );
}
