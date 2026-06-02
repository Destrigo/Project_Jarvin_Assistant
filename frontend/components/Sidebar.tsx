"use client";
import { useEffect, useState } from "react";
import { Mail, Calendar, Clock, ChevronRight, RefreshCw } from "lucide-react";
import { api, type Email, type CalEvent } from "@/lib/api";

function timeLabel(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  const diff = d.getDate() - now.getDate();
  const time = d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
  if (diff === 0) return `Oggi ${time}`;
  if (diff === 1) return `Domani ${time}`;
  return d.toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" }) + ` ${time}`;
}

function fromShort(from: string) {
  const match = from.match(/^(.+?)\s*</);
  return match ? match[1].replace(/"/g, "") : from.split("@")[0];
}

export default function Sidebar() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [events, setEvents] = useState<CalEvent[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const [em, ev] = await Promise.all([api.getEmails(), api.getEvents()]);
      setEmails(em.emails);
      setEvents(ev.events);
    } catch {
      // backend might not be running — silently ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  return (
    <aside
      style={{ background: "var(--surface)", borderRight: "1px solid var(--border)" }}
      className="w-64 shrink-0 flex flex-col h-full overflow-hidden"
    >
      {/* header */}
      <div
        style={{ borderBottom: "1px solid var(--border)" }}
        className="flex items-center justify-between px-4 py-3"
      >
        <span style={{ color: "var(--muted)" }} className="text-xs font-semibold uppercase tracking-wider">
          Overview
        </span>
        <button
          onClick={refresh}
          style={{ color: "var(--muted)" }}
          className="hover:opacity-70 transition-opacity"
          title="Aggiorna"
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* inbox */}
        <section className="px-3 pt-4 pb-2">
          <div className="flex items-center gap-1.5 mb-2 px-1">
            <Mail size={13} style={{ color: "var(--accent2)" }} />
            <span className="text-xs font-semibold" style={{ color: "var(--accent2)" }}>
              Inbox
            </span>
            {emails.length > 0 && (
              <span
                style={{ background: "var(--accent)", color: "#fff" }}
                className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full"
              >
                {emails.length}
              </span>
            )}
          </div>

          {emails.length === 0 ? (
            <p style={{ color: "var(--muted)" }} className="text-xs px-1 py-2">
              {loading ? "Caricamento..." : "Nessuna email non letta"}
            </p>
          ) : (
            <ul className="space-y-0.5">
              {emails.map((e) => (
                <li
                  key={e.id}
                  style={{ borderRadius: "6px" }}
                  className="px-2 py-2 hover:bg-white/5 cursor-pointer transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium truncate" style={{ color: "var(--text)" }}>
                      {fromShort(e.from)}
                    </span>
                    <ChevronRight size={10} style={{ color: "var(--muted)" }} className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <p className="text-[11px] truncate" style={{ color: "var(--muted)" }}>
                    {e.subject}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>

        <div style={{ borderTop: "1px solid var(--border)" }} className="mx-3 my-1" />

        {/* calendar */}
        <section className="px-3 pt-2 pb-4">
          <div className="flex items-center gap-1.5 mb-2 px-1">
            <Calendar size={13} style={{ color: "#34d399" }} />
            <span className="text-xs font-semibold" style={{ color: "#34d399" }}>
              Calendario
            </span>
          </div>

          {events.length === 0 ? (
            <p style={{ color: "var(--muted)" }} className="text-xs px-1 py-2">
              {loading ? "Caricamento..." : "Nessun evento questa settimana"}
            </p>
          ) : (
            <ul className="space-y-0.5">
              {events.map((e) => (
                <li
                  key={e.id}
                  style={{ borderRadius: "6px" }}
                  className="px-2 py-2 hover:bg-white/5 transition-colors"
                >
                  <p className="text-xs font-medium truncate" style={{ color: "var(--text)" }}>
                    {e.title}
                  </p>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Clock size={9} style={{ color: "var(--muted)" }} />
                    <span className="text-[11px]" style={{ color: "var(--muted)" }}>
                      {timeLabel(e.start)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </aside>
  );
}
