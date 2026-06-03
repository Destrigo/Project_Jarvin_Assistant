"use client";
import { useEffect, useState } from "react";
import { Mail, Calendar, Clock, ChevronRight, RefreshCw, X, ArrowLeft, Reply } from "lucide-react";
import { api, type Email, type EmailDetail, type CalEvent } from "@/lib/api";

type Props = { onInject?: (text: string) => void };

function timeLabel(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  const diffDays = Math.round((d.getTime() - now.getTime()) / 86_400_000);
  const time = d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
  if (diffDays === 0) return `Oggi ${time}`;
  if (diffDays === 1) return `Domani ${time}`;
  return d.toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" }) + ` ${time}`;
}

function fromShort(from: string) {
  const match = from.match(/^(.+?)\s*</);
  return match ? match[1].replace(/"/g, "") : from.split("@")[0];
}

function EmailPanel({ email, onClose, onReply }: {
  email: EmailDetail;
  onClose: () => void;
  onReply: (text: string) => void;
}) {
  return (
    <div className="slide-in-left" style={{
      position: "absolute", inset: 0, zIndex: 20,
      background: "var(--surface)", display: "flex", flexDirection: "column",
    }}>
      {/* header */}
      <div style={{ borderBottom: "1px solid var(--border)", padding: "10px 12px", flexShrink: 0 }}>
        <div className="flex items-center gap-2 mb-2">
          <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", padding: 2, lineHeight: 0 }}>
            <ArrowLeft size={14} />
          </button>
          <span style={{ color: "var(--text)", fontSize: 12, fontWeight: 700, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {email.subject}
          </span>
        </div>
        <p style={{ color: "var(--muted)", fontSize: 10 }}>Da: <span style={{ color: "var(--text)" }}>{email.from}</span></p>
        <p style={{ color: "var(--muted)", fontSize: 10 }}>{email.date}</p>
      </div>

      {/* body */}
      <div style={{ flex: 1, overflowY: "auto", padding: "12px", fontSize: 12, lineHeight: 1.7, color: "var(--text)", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
        {email.body || <span style={{ color: "var(--muted)" }}>Nessun testo</span>}
      </div>

      {/* reply button */}
      <div style={{ borderTop: "1px solid var(--border)", padding: "10px 12px", flexShrink: 0 }}>
        <button
          onClick={() => onReply(`Rispondi all'email di ${email.from} con oggetto "${email.subject}": `)}
          style={{
            width: "100%", background: "var(--surface2)", border: "1px solid var(--border)",
            borderRadius: 8, color: "var(--accent2)", fontSize: 11, fontWeight: 700,
            display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
            padding: "8px 0", cursor: "pointer", transition: "border-color 0.15s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent2)")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
        >
          <Reply size={12} />
          Rispondi via Jarvis
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({ onInject }: Props) {
  const [emails,       setEmails]       = useState<Email[]>([]);
  const [events,       setEvents]       = useState<CalEvent[]>([]);
  const [loading,      setLoading]      = useState(false);
  const [detailEmail,  setDetailEmail]  = useState<EmailDetail | null>(null);
  const [loadingEmail, setLoadingEmail] = useState(false);

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

  async function openEmail(id: string) {
    setLoadingEmail(true);
    setDetailEmail(null);
    try {
      const detail = await api.getEmail(id);
      setDetailEmail(detail);
    } catch {
      // fallback: inject read-email message into chat
      const email = emails.find((e) => e.id === id);
      if (email && onInject) onInject(`Leggi l'email di ${email.from} con oggetto "${email.subject}"`);
    } finally {
      setLoadingEmail(false);
    }
  }

  function handleReply(text: string) {
    setDetailEmail(null);
    onInject?.(text);
  }

  return (
    <aside
      style={{ background: "var(--surface)", borderRight: "1px solid var(--border)", position: "relative" }}
      className="w-64 shrink-0 flex flex-col h-full overflow-hidden"
    >
      {/* email detail overlay */}
      {detailEmail && (
        <EmailPanel
          email={detailEmail}
          onClose={() => setDetailEmail(null)}
          onReply={handleReply}
        />
      )}

      {/* loading overlay for email fetch */}
      {loadingEmail && (
        <div style={{ position: "absolute", inset: 0, zIndex: 15, background: "var(--surface)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <p style={{ color: "var(--muted)", fontSize: 12 }}>Caricamento email...</p>
        </div>
      )}

      {/* header */}
      <div style={{ borderBottom: "1px solid var(--border)" }} className="flex items-center justify-between px-4 py-3">
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
              <span style={{ background: "var(--accent2)", color: "#fff" }} className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full">
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
                  onClick={() => openEmail(e.id)}
                  style={{ borderRadius: "6px", cursor: "pointer" }}
                  className="px-2 py-2 hover:bg-white/5 transition-colors group"
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
                  onClick={() => onInject?.(`Dimmi i dettagli dell'evento "${e.title}" del ${e.start}`)}
                  style={{ borderRadius: "6px", cursor: onInject ? "pointer" : "default" }}
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
