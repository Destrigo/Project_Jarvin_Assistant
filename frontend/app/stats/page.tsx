"use client";
import { useEffect, useState } from "react";
import { Brain, MessageSquare, CheckCircle, Clock, BookOpen, FileText } from "lucide-react";
import { api, type Stats } from "@/lib/api";

function Card({ icon, label, value, sub, color }: {
  icon: React.ReactNode; label: string; value: string | number;
  sub?: string; color?: string;
}) {
  return (
    <div
      style={{ background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: 14 }}
      className="p-5 flex flex-col gap-3"
    >
      <div className="flex items-center gap-2">
        <div style={{ color: color ?? "var(--accent2)" }}>{icon}</div>
        <span style={{ color: "var(--muted)", fontSize: 12 }} className="uppercase tracking-wider font-semibold">
          {label}
        </span>
      </div>
      <span style={{ color: "var(--text)", fontSize: 32, fontWeight: 700, lineHeight: 1 }}>
        {value}
      </span>
      {sub && <span style={{ color: "var(--muted)", fontSize: 12 }}>{sub}</span>}
    </div>
  );
}

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.getStats().then(setStats).catch(() => setError(true));
  }, []);

  if (error) return (
    <div className="flex items-center justify-center h-full">
      <p style={{ color: "var(--muted)" }}>Backend non raggiungibile</p>
    </div>
  );

  if (!stats) return (
    <div className="flex items-center justify-center h-full">
      <p style={{ color: "var(--muted)" }}>Caricamento...</p>
    </div>
  );

  const approvalRate = stats.approvals.resolved > 0
    ? Math.round(stats.approvals.resolved / (stats.approvals.resolved + stats.approvals.pending) * 100)
    : 0;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 style={{ color: "var(--text)", fontSize: 22, fontWeight: 700 }} className="mb-6">
        Le tue statistiche
      </h1>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <Card
          icon={<Brain size={18} />}
          label="Note in memoria"
          value={stats.vault.total_notes}
          sub={`${stats.vault.memory_notes} fatti · ${stats.vault.conversation_notes} conversazioni`}
          color="var(--accent2)"
        />
        <Card
          icon={<MessageSquare size={18} />}
          label="Messaggi totali"
          value={stats.conversations.total_messages}
          sub={`${stats.conversations.user_messages} tuoi · ${stats.conversations.total_messages - stats.conversations.user_messages} di Jarvis`}
          color="#60a5fa"
        />
        <Card
          icon={<CheckCircle size={18} />}
          label="Azioni risolte"
          value={stats.approvals.resolved}
          sub={`${approvalRate}% approvate`}
          color="#34d399"
        />
        <Card
          icon={<Clock size={18} />}
          label="In attesa"
          value={stats.approvals.pending}
          sub="approvazioni pendenti"
          color={stats.approvals.pending > 0 ? "#f59e0b" : "var(--muted)"}
        />
      </div>

      <div
        style={{ background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: 14 }}
        className="p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <BookOpen size={16} style={{ color: "var(--accent2)" }} />
          <span style={{ color: "var(--muted)", fontSize: 12 }} className="uppercase tracking-wider font-semibold">
            Vault Obsidian
          </span>
        </div>
        <div className="flex gap-8">
          {[
            { label: "Totale", value: stats.vault.total_notes, color: "var(--text)" },
            { label: "Memoria", value: stats.vault.memory_notes, color: "#a78bfa" },
            { label: "Conversazioni", value: stats.vault.conversation_notes, color: "#34d399" },
          ].map(({ label, value, color }) => (
            <div key={label} className="flex flex-col gap-1">
              <span style={{ color, fontSize: 28, fontWeight: 700 }}>{value}</span>
              <span style={{ color: "var(--muted)", fontSize: 12 }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
