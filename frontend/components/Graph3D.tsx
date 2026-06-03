"use client";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { X, FileText, Search, RefreshCw } from "lucide-react";
import { api, type GraphData, type GraphNode } from "@/lib/api";

const FOLDER_COLORS: Record<string, string> = {
  Memoria:       "#a78bfa",
  Conversazioni: "#34d399",
  Wiki:          "#00f0ff",
  Fonti:         "#f59e0b",
  "":            "#6c63ff",
};
function folderColor(f: string) { return FOLDER_COLORS[f] ?? "#60a5fa"; }

type NotePanel = { title: string; content: string; folder: string } | null;

export default function Graph3D() {
  const containerRef  = useRef<HTMLDivElement>(null);
  const fgRef         = useRef<any>(null);
  const [data,        setData]        = useState<GraphData | null>(null);
  const [note,        setNote]        = useState<NotePanel>(null);
  const [loadingNote, setLoadingNote] = useState(false);
  const [error,       setError]       = useState<string | null>(null);
  const [query,       setQuery]       = useState("");
  const [results,     setResults]     = useState<GraphNode[]>([]);
  const [nodeCount,   setNodeCount]   = useState(0);
  const [linkCount,   setLinkCount]   = useState(0);

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

  function load() {
    api.getMemoryGraph()
      .then((d) => { setData(d); setNodeCount(d.nodes.length); setLinkCount(d.links.length); })
      .catch(() => setError("Backend non raggiungibile"));
  }

  useEffect(() => { load(); }, []);

  useEffect(() => {
    if (!data || !containerRef.current) return;

    // precompute degree for each node
    const degree = new Map<number, number>();
    data.nodes.forEach((n) => degree.set(n.id, 0));
    data.links.forEach((l) => {
      degree.set(l.source as number, (degree.get(l.source as number) ?? 0) + 1);
      degree.set(l.target as number, (degree.get(l.target as number) ?? 0) + 1);
    });
    const maxDeg = Math.max(1, ...degree.values());

    let fg: any;
    import("3d-force-graph").then((mod) => {
      if (!containerRef.current) return;
      const ForceGraph3D = (mod as any).default;
      fg = ForceGraph3D()(containerRef.current)
        .width(containerRef.current.clientWidth)
        .height(containerRef.current.clientHeight)
        .backgroundColor("#030308")

        // nodes — size and brightness by degree
        .nodeLabel((n: any) => n.name)
        .nodeVal((n: any) => {
          const deg = degree.get(n.id) ?? 0;
          return Math.max(0.8, (deg / maxDeg) * 6 + 0.8);
        })
        .nodeColor((n: any) => {
          const deg = degree.get(n.id) ?? 0;
          const alpha = Math.round(140 + (deg / maxDeg) * 115).toString(16).padStart(2, "0");
          return folderColor(n.folder) + alpha;
        })
        .nodeOpacity(1)
        .nodeResolution(16)

        // edges — very thin, dim, with particle flow
        .linkColor(() => "#ffffff0a")
        .linkOpacity(1)
        .linkWidth(0.3)
        .linkDirectionalParticles(2)
        .linkDirectionalParticleSpeed(0.004)
        .linkDirectionalParticleWidth(0.7)
        .linkDirectionalParticleColor((l: any) => {
          const src = data.nodes.find((n) => n.id === (l.source?.id ?? l.source));
          return src ? folderColor(src.folder) + "cc" : "#00f0ffcc";
        })

        .onNodeClick((n: any) => openNoteRef.current(n.name))
        .onNodeHover((n: any) => {
          if (containerRef.current) {
            containerRef.current.style.cursor = n ? "pointer" : "default";
          }
        })
        .graphData(data);

      fg.d3Force("charge")?.strength(-120);
      fg.d3Force("link")?.distance(30);
      fgRef.current = fg;
    });

    return () => { fg?.pauseAnimation?.(); };
  }, [data]);

  // live search
  useEffect(() => {
    if (!data || !fgRef.current) return;
    const q = query.trim().toLowerCase();
    if (!q) {
      setResults([]);
      const degree = new Map<number, number>();
      data.nodes.forEach((n) => degree.set(n.id, 0));
      data.links.forEach((l) => {
        degree.set(l.source as number, (degree.get(l.source as number) ?? 0) + 1);
        degree.set(l.target as number, (degree.get(l.target as number) ?? 0) + 1);
      });
      const maxDeg = Math.max(1, ...degree.values());
      fgRef.current.nodeColor((n: any) => {
        const deg = degree.get(n.id) ?? 0;
        const alpha = Math.round(140 + (deg / maxDeg) * 115).toString(16).padStart(2, "0");
        return folderColor(n.folder) + alpha;
      });
      return;
    }
    const matched = data.nodes.filter((n) => n.name.toLowerCase().includes(q));
    setResults(matched.slice(0, 10));
    const matchedIds = new Set(matched.map((n) => n.id));
    fgRef.current.nodeColor((n: any) =>
      matchedIds.has(n.id) ? "#ffffff" : "#ffffff08"
    );
  }, [query, data]);

  function flyTo(node: GraphNode) {
    if (!fgRef.current) return;
    const { x = 0, y = 0, z = 0 } = (node as any);
    fgRef.current.cameraPosition({ x: x + 40, y: y + 20, z: z + 40 }, { x, y, z }, 1200);
    openNoteRef.current(node.name);
    setQuery("");
    setResults([]);
  }

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", background: "#030308" }}>
      {/* 3D canvas */}
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {/* top-left: legend + search */}
      <div style={{ position: "absolute", top: 12, left: 12, display: "flex", flexDirection: "column", gap: 8, maxWidth: 200 }}>

        {/* stats bar */}
        <div style={{ background: "rgba(3,3,8,0.85)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 10px", display: "flex", gap: 12, alignItems: "center" }}>
          <span style={{ color: "var(--muted)", fontSize: 10 }}>{nodeCount} note</span>
          <span style={{ color: "var(--border)", fontSize: 10 }}>·</span>
          <span style={{ color: "var(--muted)", fontSize: 10 }}>{linkCount} link</span>
          <button onClick={load} style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", padding: 0, lineHeight: 0, marginLeft: "auto" }} title="Ricarica">
            <RefreshCw size={10} />
          </button>
        </div>

        {/* folder legend */}
        <div style={{ background: "rgba(3,3,8,0.85)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 10px", display: "flex", flexDirection: "column", gap: 4 }}>
          {Object.entries(FOLDER_COLORS).map(([folder, color]) => (
            <div key={folder} style={{ display: "flex", alignItems: "center", gap: 7 }}>
              <div style={{ width: 7, height: 7, borderRadius: "50%", background: color, boxShadow: `0 0 4px ${color}` }} />
              <span style={{ color: "var(--muted)", fontSize: 10 }}>{folder || "Root"}</span>
            </div>
          ))}
        </div>

        {/* search */}
        <div style={{ background: "rgba(3,3,8,0.85)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 10px" }}>
            <Search size={11} color="var(--muted)" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Cerca nota..."
              style={{ background: "transparent", border: "none", outline: "none", color: "var(--text)", fontSize: 11, width: "100%", fontFamily: "inherit" }}
            />
            {query && (
              <button onClick={() => setQuery("")} style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", padding: 0, lineHeight: 0, flexShrink: 0 }}>
                <X size={9} />
              </button>
            )}
          </div>
          {results.length > 0 && (
            <div style={{ borderTop: "1px solid var(--border)", maxHeight: 200, overflowY: "auto" }}>
              {results.map((n) => (
                <button key={n.id} onClick={() => flyTo(n)} style={{
                  display: "flex", alignItems: "center", gap: 7,
                  width: "100%", padding: "5px 10px",
                  background: "none", border: "none", cursor: "pointer", textAlign: "left",
                  transition: "background 0.1s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface2)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
                >
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: folderColor(n.folder), boxShadow: `0 0 3px ${folderColor(n.folder)}`, flexShrink: 0 }} />
                  <span style={{ color: "var(--text)", fontSize: 11, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{n.name}</span>
                  {n.folder && <span style={{ color: "var(--muted)", fontSize: 9, flexShrink: 0 }}>{n.folder}</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* note panel */}
      {(note || loadingNote) && (
        <div className="slide-in-right" style={{
          position: "absolute", top: 0, right: 0, bottom: 0, width: 340,
          background: "rgba(11,11,26,0.96)", backdropFilter: "blur(12px)",
          borderLeft: "1px solid var(--border)",
          display: "flex", flexDirection: "column", zIndex: 10,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 14px", borderBottom: "1px solid var(--border)", flexShrink: 0 }}>
            <FileText size={14} color="var(--accent2)" />
            <span style={{ color: "var(--text)", fontSize: 13, fontWeight: 600, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {loadingNote ? "Caricamento..." : note?.title}
            </span>
            {note?.folder && (
              <span style={{ fontSize: 10, color: folderColor(note.folder), background: folderColor(note.folder) + "22", border: `1px solid ${folderColor(note.folder)}44`, borderRadius: 4, padding: "1px 6px", flexShrink: 0 }}>
                {note.folder}
              </span>
            )}
            <button onClick={() => setNote(null)} style={{ color: "var(--muted)", flexShrink: 0, background: "none", border: "none", cursor: "pointer", padding: 2 }}>
              <X size={14} />
            </button>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px" }}>
            {loadingNote ? (
              <p style={{ color: "var(--muted)", fontSize: 13 }}>Caricamento...</p>
            ) : (
              <ReactMarkdown components={{
                h1: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 700, fontSize: 14, margin: "8px 0 4px" }}>{children}</p>,
                h2: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 600, fontSize: 13, margin: "6px 0 3px" }}>{children}</p>,
                p: ({ children }) => <p style={{ color: "var(--text)", fontSize: 12.5, lineHeight: 1.65, marginBottom: 6 }}>{children}</p>,
                strong: ({ children }) => <strong style={{ color: "var(--accent2)" }}>{children}</strong>,
                em: ({ children }) => <em style={{ color: "var(--muted)" }}>{children}</em>,
                ul: ({ children }) => <ul style={{ paddingLeft: 14, marginBottom: 6 }}>{children}</ul>,
                li: ({ children }) => <li style={{ color: "var(--text)", fontSize: 12.5, lineHeight: 1.6, marginBottom: 2 }}>{children}</li>,
                hr: () => <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "8px 0" }} />,
                code: ({ children }) => <code style={{ background: "rgba(0,0,0,0.3)", borderRadius: 3, padding: "1px 5px", fontSize: 11, color: "#34d399" }}>{children}</code>,
              }}>
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
