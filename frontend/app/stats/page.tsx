"use client";
import { useEffect, useState } from "react";
import { Brain, MessageSquare, CheckCircle, Clock, BookOpen, RefreshCw } from "lucide-react";
import { api, type Stats } from "@/lib/api";

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div style={{ height: 4, background: "var(--surface)", borderRadius: 2, overflow: "hidden", marginTop: 8 }}>
      <div style={{
        width: `${pct}%`, height: "100%",
        background: color,
        boxShadow: `0 0 6px ${color}`,
        borderRadius: 2,
        transition: "width 0.6s ease",
      }} />
    </div>
  );
}

function Card({ icon, label, value, sub, color, barValue, barMax }: {
  icon: React.ReactNode; label: string; value: string | number;
  sub?: string; color?: string; barValue?: number; barMax?: number;
}) {
  return (
    <div style={{ background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: 14 }} className="p-5 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <div style={{ color: color ?? "var(--accent2)" }}>{icon}</div>
        <span style={{ color: "var(--muted)", fontSize: 12 }} className="uppercase tracking-wider font-semibold">
          {label}
        </span>
      </div>
      <span style={{ color: "var(--text)", fontSize: 32, fontWeight: 700, lineHeight: 1 }}>{value}</span>
      {sub && <span style={{ color: "var(--muted)", fontSize: 12 }}>{sub}</span>}
      {barValue !== undefined && barMax !== undefined && (
        <Bar value={barValue} max={barMax} color={color ?? "var(--accent2)"} />
      )}
    </div>
  );
}

export default function StatsPage() {
  const [stats,    setStats]   = useState<Stats | null>(null);
  const [error,    setError]   = useState(false);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  async function load() {
    try {
      const s = await api.getStats();
      setStats(s);
      setLastSync(new Date());
      setError(false);
    } catch {
      setError(true);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 30_000);
    return () => clearInterval(t);
  }, []);

  if (error) return (
    <div className="flex flex-col items-center justify-center h-full gap-3">
      <p style={{ color: "var(--muted)" }}>Backend non raggiungibile</p>
      <button
        onClick={load}
        style={{ background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)", fontSize: 12, padding: "6px 14px", cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}
      >
        <RefreshCw size={12} /> Riprova
      </button>
    </div>
  );

  if (!stats) return (
    <div className="flex items-center justify-center h-full">
      <p style={{ color: "var(--muted)" }}>Caricamento...</p>
    </div>
  );

  const totalApprovals = stats.approvals.resolved + stats.approvals.pending;
  const approvalRate = totalApprovals > 0
    ? Math.round(stats.approvals.resolved / totalApprovals * 100) : 0;

  return (
    <div className="p-6 max-w-3xl mx-auto overflow-y-auto" style={{ height: "calc(100dvh - 49px)" }}>
      <div className="flex items-center justify-between mb-6">
        <h1 style={{ color: "var(--text)", fontSize: 22, fontWeight: 700 }}>
          Le tue statistiche
        </h1>
        <div className="flex items-center gap-3">
          {lastSync && (
            <span style={{ color: "var(--muted)", fontSize: 10 }}>
              sync {lastSync.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          )}
          <button
            onClick={load}
            style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", padding: 4, lineHeight: 0 }}
            title="Aggiorna ora"
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <Card
          icon={<Brain size={18} />}
          label="Note in memoria"
          value={stats.vault.total_notes}
          sub={`${stats.vault.memory_notes} fatti · ${stats.vault.conversation_notes} conversazioni`}
          color="var(--accent2)"
          barValue={stats.vault.memory_notes}
          barMax={stats.vault.total_notes}
        />
        <Card
          icon={<MessageSquare size={18} />}
          label="Messaggi totali"
          value={stats.conversations.total_messages}
          sub={`${stats.conversations.user_messages} tuoi · ${stats.conversations.total_messages - stats.conversations.user_messages} di Jarvis`}
          color="#60a5fa"
          barValue={stats.conversations.user_messages}
          barMax={stats.conversations.total_messages}
        />
        <Card
          icon={<CheckCircle size={18} />}
          label="Azioni risolte"
          value={stats.approvals.resolved}
          sub={`${approvalRate}% approvate`}
          color="#34d399"
          barValue={stats.approvals.resolved}
          barMax={totalApprovals || 1}
        />
        <Card
          icon={<Clock size={18} />}
          label="In attesa"
          value={stats.approvals.pending}
          sub="approvazioni pendenti"
          color={stats.approvals.pending > 0 ? "#f59e0b" : "var(--muted)"}
        />
      </div>

      {/* vault breakdown */}
      <div style={{ background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: 14 }} className="p-5">
        <div className="flex items-center gap-2 mb-5">
          <BookOpen size={16} style={{ color: "var(--accent2)" }} />
          <span style={{ color: "var(--muted)", fontSize: 12 }} className="uppercase tracking-wider font-semibold">
            Vault Obsidian
          </span>
        </div>
        <div className="flex gap-8 mb-5">
          {[
            { label: "Totale",        value: stats.vault.total_notes,        color: "var(--text)" },
            { label: "Memoria",       value: stats.vault.memory_notes,       color: "#a78bfa" },
            { label: "Conversazioni", value: stats.vault.conversation_notes, color: "#34d399" },
          ].map(({ label, value, color }) => (
            <div key={label} className="flex flex-col gap-1">
              <span style={{ color, fontSize: 28, fontWeight: 700 }}>{value}</span>
              <span style={{ color: "var(--muted)", fontSize: 12 }}>{label}</span>
            </div>
          ))}
        </div>

        {/* stacked bar */}
        <div style={{ height: 8, background: "var(--surface)", borderRadius: 4, overflow: "hidden", display: "flex" }}>
          {stats.vault.total_notes > 0 && (
            <>
              <div style={{ width: `${stats.vault.memory_notes / stats.vault.total_notes * 100}%`, background: "#a78bfa", boxShadow: "0 0 6px #a78bfa", transition: "width 0.6s" }} />
              <div style={{ width: `${stats.vault.conversation_notes / stats.vault.total_notes * 100}%`, background: "#34d399", boxShadow: "0 0 6px #34d399", transition: "width 0.6s" }} />
            </>
          )}
        </div>
        <div className="flex gap-4 mt-3">
          {[["#a78bfa", "Memoria"], ["#34d399", "Conversazioni"], ["var(--muted)", "Root"]].map(([c, l]) => (
            <div key={l} className="flex items-center gap-1.5">
              <div style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
              <span style={{ color: "var(--muted)", fontSize: 11 }}>{l}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
