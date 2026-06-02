"use client";
import { useEffect, useRef, useState, useCallback, memo } from "react";
import { Send, Volume2, VolumeX, Mail, Calendar, FileText, Sparkles, Bot } from "lucide-react";
import ReactMarkdown, { Components } from "react-markdown";
import { api, type Message, type PendingAction } from "@/lib/api";
import PendingBanner from "./PendingBanner";
import JarvisAvatar, { type AvatarState } from "./JarvisAvatar";

// Defined once outside component — no re-creation on every keystroke
const MD: Components = {
  h1: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 700, fontSize: 15, margin: "8px 0 4px" }}>{children}</p>,
  h2: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 700, fontSize: 14, margin: "8px 0 4px" }}>{children}</p>,
  h3: ({ children }) => <p style={{ color: "var(--accent2)", fontWeight: 600, fontSize: 13.5, margin: "6px 0 3px" }}>{children}</p>,
  p: ({ children }) => <p style={{ color: "var(--text)", fontSize: 13.5, lineHeight: 1.7, margin: "0 0 6px" }}>{children}</p>,
  strong: ({ children }) => <strong style={{ color: "var(--accent2)", fontWeight: 600 }}>{children}</strong>,
  em: ({ children }) => <em style={{ color: "var(--muted)" }}>{children}</em>,
  ul: ({ children }) => <ul style={{ paddingLeft: 16, margin: "4px 0 6px" }}>{children}</ul>,
  ol: ({ children }) => <ol style={{ paddingLeft: 16, margin: "4px 0 6px" }}>{children}</ol>,
  li: ({ children }) => <li style={{ color: "var(--text)", fontSize: 13.5, lineHeight: 1.65, marginBottom: 3 }}>{children}</li>,
  hr: () => <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "10px 0" }} />,
  code: ({ children }) => <code style={{ background: "rgba(0,0,0,0.35)", border: "1px solid var(--border)", borderRadius: 4, padding: "1px 6px", fontSize: 12, color: "#34d399", fontFamily: "monospace" }}>{children}</code>,
  blockquote: ({ children }) => <blockquote style={{ borderLeft: "3px solid var(--accent)", paddingLeft: 10, margin: "6px 0", opacity: 0.85 }}>{children}</blockquote>,
};

// ── Typing dots ────────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex gap-1 items-center" style={{ padding: "4px 2px" }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: 7, height: 7,
            borderRadius: "50%",
            background: "var(--accent2)",
            display: "inline-block",
            animation: `dotBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
      <style>{`
        @keyframes dotBounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// ── Message bubble — memoized so it never re-renders on input change ──────────
const Bubble = memo(function Bubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-2.5 group ${isUser ? "flex-row-reverse" : ""}`}>
      {/* avatar */}
      <div
        style={{
          background: isUser ? "var(--accent)" : "#1e1e2e",
          border: isUser ? "none" : "1px solid var(--border)",
          borderRadius: "50%",
          flexShrink: 0,
          width: 30, height: 30,
          display: "flex", alignItems: "center", justifyContent: "center",
          marginTop: 2,
        }}
      >
        {isUser
          ? <span style={{ color: "#fff", fontSize: 12, fontWeight: 700 }}>Tu</span>
          : <Bot size={14} color="var(--accent2)" />}
      </div>

      {/* bubble */}
      <div style={{ maxWidth: "78%", display: "flex", flexDirection: "column", gap: 2 }}>
        <div
          style={{
            background: isUser ? "var(--accent)" : "var(--surface2)",
            border: isUser ? "none" : "1px solid var(--border)",
            borderRadius: isUser ? "18px 4px 18px 18px" : "4px 18px 18px 18px",
            padding: isUser ? "9px 14px" : "12px 16px",
            wordBreak: "break-word",
          }}
        >
          {isUser ? (
            <p style={{ color: "#fff", fontSize: 13.5, lineHeight: 1.6, margin: 0 }}>
              {msg.content}
            </p>
          ) : (
            <ReactMarkdown components={MD}>{msg.content}</ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
});

// ── Suggestion chips ────────────────────────────────────────────────────────────
const SUGGESTIONS = [
  { icon: Mail,     text: "Controlla le email non lette" },
  { icon: Calendar, text: "Cosa ho in calendario oggi?" },
  { icon: FileText, text: "Riassumi le ultime 5 email" },
  { icon: Sparkles, text: "Cosa sai di me?" },
];

// ── TTS helper ─────────────────────────────────────────────────────────────────
function speak(text: string, onStart: () => void, onEnd: () => void) {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const plain = text.replace(/[#*`_~>]/g, "").replace(/\n+/g, " ").trim();
  const utt = new SpeechSynthesisUtterance(plain);
  utt.lang = "it-IT";
  utt.rate = 1.05;
  utt.pitch = 1;
  // prefer Italian voice if available
  const voices = window.speechSynthesis.getVoices();
  const itVoice = voices.find((v) => v.lang.startsWith("it"));
  if (itVoice) utt.voice = itVoice;
  utt.onstart = onStart;
  utt.onend = onEnd;
  utt.onerror = onEnd;
  window.speechSynthesis.speak(utt);
}

// ── Main chat ──────────────────────────────────────────────────────────────────
export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<PendingAction[]>([]);
  const [focused, setFocused] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [avatarState, setAvatarState] = useState<AvatarState>("idle");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  async function loadHistory() {
    try { setMessages((await api.getHistory()).messages); } catch {}
  }
  async function loadPending() {
    try { setPending((await api.getPending()).pending); } catch {}
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

  // Auto-resize textarea
  const autoResize = useCallback((el: HTMLTextAreaElement) => {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, []);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", content: text.trim() }]);
    setInput("");
    if (inputRef.current) { inputRef.current.style.height = "auto"; }
    setLoading(true);
    setAvatarState("thinking");
    try {
      const res = await api.sendTask(text.trim());
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      await loadPending();
      if (ttsEnabled) {
        speak(res.reply,
          () => setAvatarState("speaking"),
          () => setAvatarState("idle")
        );
      } else {
        setAvatarState("idle");
      }
    } catch {
      setAvatarState("idle");
      setMessages((m) => [...m, { role: "assistant", content: "⚠️ Impossibile contattare il backend." }]);
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

  const canSend = input.trim().length > 0 && !loading;

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">
      <PendingBanner actions={pending} onResolved={loadPending} />

      {/* messages */}
      <div className="flex-1 overflow-y-auto px-5 py-5" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full gap-5">
            <JarvisAvatar state={avatarState} />
            <div className="text-center">
              <h2 style={{ color: "var(--text)", fontSize: 18, fontWeight: 700 }}>Ciao, sono Jarvis</h2>
              <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 4 }}>Il tuo assistente personale. Cosa faccio per te?</p>
            </div>
            <div className="grid grid-cols-2 gap-2" style={{ maxWidth: 340, width: "100%" }}>
              {SUGGESTIONS.map(({ icon: Icon, text }) => (
                <button
                  key={text}
                  onClick={() => send(text)}
                  style={{
                    background: "var(--surface2)",
                    border: "1px solid var(--border)",
                    borderRadius: 12, padding: "10px 12px",
                    color: "var(--text)", textAlign: "left",
                    transition: "border-color 0.15s, background 0.15s",
                    display: "flex", flexDirection: "column", gap: 6,
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--accent)";
                    (e.currentTarget as HTMLElement).style.background = "var(--surface)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                    (e.currentTarget as HTMLElement).style.background = "var(--surface2)";
                  }}
                >
                  <Icon size={14} color="var(--accent2)" />
                  <span style={{ fontSize: 12, lineHeight: 1.4 }}>{text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => <Bubble key={i} msg={m} />)}

        {loading && (
          <div className="flex gap-2.5">
            <div style={{ background: "#1e1e2e", border: "1px solid var(--border)", borderRadius: "50%", width: 30, height: 30, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 2 }}>
              <Bot size={14} color="var(--accent2)" />
            </div>
            <div style={{ background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: "4px 18px 18px 18px", padding: "10px 16px" }}>
              <TypingDots />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* avatar bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "10px 16px 0", gap: 16, background: "var(--surface)" }}>
        <JarvisAvatar state={avatarState} />
        <button
          onClick={() => {
            if (ttsEnabled) window.speechSynthesis?.cancel();
            setTtsEnabled((v) => !v);
            if (avatarState === "speaking") setAvatarState("idle");
          }}
          title={ttsEnabled ? "Disattiva voce" : "Attiva voce"}
          style={{ background: "none", border: "none", cursor: "pointer", color: ttsEnabled ? "var(--accent2)" : "var(--muted)", padding: 4 }}
        >
          {ttsEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
        </button>
      </div>

      {/* input area */}
      <div style={{ borderTop: "none", background: "var(--surface)", padding: "8px 16px 14px" }}>
        <div
          style={{
            background: "var(--surface2)",
            border: `1px solid ${focused ? "var(--accent)" : "var(--border)"}`,
            borderRadius: 16,
            display: "flex",
            alignItems: "flex-end",
            gap: 8,
            padding: "10px 10px 10px 16px",
            transition: "border-color 0.15s",
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              autoResize(e.target);
            }}
            onKeyDown={onKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Scrivi un messaggio…"
            rows={1}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text)",
              fontSize: "13.5px",
              lineHeight: "1.6",
              resize: "none",
              flex: 1,
              minHeight: 24,
              maxHeight: 200,
              overflowY: "auto",
              fontFamily: "inherit",
              padding: 0,
            }}
            autoFocus
          />
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4, flexShrink: 0 }}>
            <button
              onClick={() => send(input)}
              disabled={!canSend}
              style={{
                background: canSend ? "var(--accent)" : "var(--border)",
                borderRadius: 10,
                width: 34, height: 34,
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.15s, transform 0.1s",
                cursor: canSend ? "pointer" : "default",
                border: "none",
              }}
              onMouseDown={(e) => canSend && ((e.currentTarget as HTMLElement).style.transform = "scale(0.92)")}
              onMouseUp={(e) => ((e.currentTarget as HTMLElement).style.transform = "scale(1)")}
            >
              <Send size={14} color="#fff" />
            </button>
          </div>
        </div>
        <p style={{ color: "var(--muted)", fontSize: 11, textAlign: "center", marginTop: 6 }}>
          Enter per inviare · Shift+Enter per andare a capo
        </p>
      </div>
    </div>
  );
}
