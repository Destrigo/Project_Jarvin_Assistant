"use client";
import { useEffect, useRef, useState } from "react";
import { Send, Loader2, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api, type Message, type PendingAction } from "@/lib/api";
import PendingBanner from "./PendingBanner";

function Bubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        style={{
          background: isUser ? "var(--accent)" : "var(--surface2)",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          flexShrink: 0,
          width: 28,
          height: 28,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {isUser ? <User size={14} color="#fff" /> : <Bot size={14} color="var(--accent2)" />}
      </div>
      <div
        style={{
          background: isUser ? "var(--accent)" : "var(--surface2)",
          borderRadius: isUser ? "18px 4px 18px 18px" : "4px 18px 18px 18px",
          maxWidth: "75%",
          padding: "10px 14px",
          wordBreak: "break-word",
        }}
        className="md-bubble"
      >
        {isUser ? (
          <span style={{ color: "#fff", fontSize: 13, lineHeight: 1.6 }}>{msg.content}</span>
        ) : (
          <ReactMarkdown
            components={{
              h1: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 700, fontSize: 15, marginBottom: 6, marginTop: 8 }}>{children}</p>,
              h2: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 700, fontSize: 14, marginBottom: 4, marginTop: 8 }}>{children}</p>,
              h3: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 600, fontSize: 13, marginBottom: 4, marginTop: 8 }}>{children}</p>,
              p: ({ children }) => <p style={{ color: "var(--text)", fontSize: 13, lineHeight: 1.65, marginBottom: 6 }}>{children}</p>,
              strong: ({ children }) => <strong style={{ color: "var(--accent2)", fontWeight: 600 }}>{children}</strong>,
              em: ({ children }) => <em style={{ color: "var(--muted)" }}>{children}</em>,
              ul: ({ children }) => <ul style={{ paddingLeft: 18, marginBottom: 6 }}>{children}</ul>,
              ol: ({ children }) => <ol style={{ paddingLeft: 18, marginBottom: 6 }}>{children}</ol>,
              li: ({ children }) => <li style={{ color: "var(--text)", fontSize: 13, lineHeight: 1.65, marginBottom: 2 }}>{children}</li>,
              hr: () => <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "10px 0" }} />,
              code: ({ children }) => <code style={{ background: "rgba(0,0,0,0.3)", borderRadius: 4, padding: "1px 5px", fontSize: 12, color: "#34d399" }}>{children}</code>,
              blockquote: ({ children }) => <blockquote style={{ borderLeft: "3px solid var(--accent)", paddingLeft: 10, margin: "6px 0", opacity: 0.8 }}>{children}</blockquote>,
            }}
          >
            {msg.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}

const SUGGESTIONS = [
  "Controlla le email non lette",
  "Cosa ho in calendario oggi?",
  "Riassumi le ultime 5 email",
  "Crea un evento per domani alle 10",
];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<PendingAction[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  async function loadHistory() {
    try {
      const h = await api.getHistory();
      setMessages(h.messages);
    } catch {}
  }

  async function loadPending() {
    try {
      const p = await api.getPending();
      setPending(p.pending);
    } catch {}
  }

  useEffect(() => {
    loadHistory();
    loadPending();
    const t = setInterval(loadPending, 10_000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    const userMsg: Message = { role: "user", content: text.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.sendTask(text.trim());
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      await loadPending();
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `⚠️ Errore: impossibile contattare il backend.` },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">
      {/* pending approvals banner */}
      <PendingBanner actions={pending} onResolved={loadPending} />

      {/* messages */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <div style={{ color: "var(--accent2)" }}>
              <Bot size={40} strokeWidth={1.5} />
            </div>
            <div className="text-center">
              <h2 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
                Ciao, sono Jarvis
              </h2>
              <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>
                Cosa posso fare per te?
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 max-w-sm w-full">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  style={{
                    background: "var(--surface2)",
                    border: "1px solid var(--border)",
                    borderRadius: "10px",
                    color: "var(--text)",
                  }}
                  className="text-xs px-3 py-2.5 text-left hover:opacity-70 transition-opacity leading-snug"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}

        {loading && (
          <div className="flex gap-3">
            <div
              style={{
                background: "var(--surface2)",
                borderRadius: "18px 18px 18px 4px",
                width: 28,
                height: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <Bot size={14} color="var(--accent2)" />
            </div>
            <div
              style={{
                background: "var(--surface2)",
                borderRadius: "4px 18px 18px 18px",
                padding: "10px 16px",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <Loader2 size={13} className="animate-spin" style={{ color: "var(--accent2)" }} />
              <span style={{ color: "var(--muted)", fontSize: "13px" }}>Pensando...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* input */}
      <div
        style={{ borderTop: "1px solid var(--border)", background: "var(--surface)" }}
        className="px-4 py-3"
      >
        <div
          style={{
            background: "var(--surface2)",
            border: "1px solid var(--border)",
            borderRadius: "14px",
            display: "flex",
            alignItems: "flex-end",
            gap: 8,
            padding: "8px 8px 8px 14px",
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
        >
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Scrivi un messaggio… (Shift+Enter per andare a capo)"
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text)",
              fontSize: "13px",
              lineHeight: "1.5",
              resize: "none",
              flex: 1,
              maxHeight: "120px",
              overflowY: "auto",
            }}
            autoFocus
          />
          <button
            onClick={() => send(input)}
            disabled={!input.trim() || loading}
            style={{
              background: input.trim() && !loading ? "var(--accent)" : "var(--border)",
              borderRadius: "9px",
              width: 32,
              height: 32,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background 0.15s",
              flexShrink: 0,
            }}
          >
            <Send size={14} color="#fff" />
          </button>
        </div>
        <p style={{ color: "var(--muted)", fontSize: "10px" }} className="text-center mt-1.5">
          Le azioni di scrittura richiedono approvazione su Telegram
        </p>
      </div>
    </div>
  );
}
