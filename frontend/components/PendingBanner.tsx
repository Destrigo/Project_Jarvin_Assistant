"use client";
import { useState } from "react";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api, type PendingAction } from "@/lib/api";

type Props = { actions: PendingAction[]; onResolved: () => void };

export default function PendingBanner({ actions, onResolved }: Props) {
  const [busy, setBusy] = useState<string | null>(null);

  if (actions.length === 0) return null;

  async function resolve(id: string, status: "approved" | "skipped") {
    setBusy(id + status);
    try {
      await api.resolve(id, status);
      onResolved();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div style={{ background: "#1a1520", borderBottom: "1px solid #3b2f6e" }}
         className="px-4 py-2 flex flex-col gap-2">
      <p style={{ color: "var(--accent2)" }} className="text-xs font-semibold uppercase tracking-wide">
        {actions.length} azione{actions.length > 1 ? "i" : ""} in attesa
      </p>
      {actions.map((a) => (
        <div key={a.id} className="flex items-start gap-3">
          <div className="text-xs flex-1 leading-snug" style={{ color: "var(--text)" }}>
            <ReactMarkdown components={{
              p: ({ children }) => <p style={{ margin: 0, fontSize: 12, color: "var(--text)" }}>{children}</p>,
              strong: ({ children }) => <strong style={{ color: "var(--accent2)" }}>{children}</strong>,
              em: ({ children }) => <em style={{ color: "var(--muted)" }}>{children}</em>,
              code: ({ children }) => <code style={{ background: "rgba(0,0,0,0.3)", borderRadius: 3, padding: "1px 4px", fontSize: 11, color: "#34d399" }}>{children}</code>,
            }}>
              {a.description}
            </ReactMarkdown>
          </div>
          <div className="flex gap-1.5 shrink-0">
            <button
              onClick={() => resolve(a.id, "approved")}
              disabled={!!busy}
              style={{ background: "#14532d", color: "#4ade80", borderRadius: "5px" }}
              className="flex items-center gap-1 text-[11px] font-medium px-2 py-1 hover:opacity-80 transition-opacity disabled:opacity-40"
            >
              {busy === a.id + "approved" ? <Loader2 size={11} className="animate-spin" /> : <CheckCircle size={11} />}
              Approva
            </button>
            <button
              onClick={() => resolve(a.id, "skipped")}
              disabled={!!busy}
              style={{ background: "#450a0a", color: "#f87171", borderRadius: "5px" }}
              className="flex items-center gap-1 text-[11px] font-medium px-2 py-1 hover:opacity-80 transition-opacity disabled:opacity-40"
            >
              {busy === a.id + "skipped" ? <Loader2 size={11} className="animate-spin" /> : <XCircle size={11} />}
              Salta
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
