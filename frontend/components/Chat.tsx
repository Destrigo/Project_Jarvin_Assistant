"use client";
import { useEffect, useRef, useState, useCallback, memo } from "react";
import { Send, Volume2, VolumeX, Mail, Calendar, FileText, Sparkles, Bot, Mic, MicOff } from "lucide-react";
import ReactMarkdown, { Components } from "react-markdown";
import { api, type Message, type PendingAction } from "@/lib/api";
import PendingBanner from "./PendingBanner";
import JarvisAvatar, { type AvatarState } from "./JarvisAvatar";

const TOOL_LABELS: Record<string, string> = {
  list_emails:            "📧 Leggendo le email...",
  read_email:             "📧 Aprendo l'email...",
  send_email:             "📧 Preparando l'email...",
  list_events:            "📅 Controllando il calendario...",
  create_event:           "📅 Creando l'evento...",
  read_file:              "📂 Leggendo il file...",
  write_file:             "📂 Scrivendo il file...",
  list_files:             "📂 Elencando i file...",
  memory_write:           "🧠 Salvando in memoria...",
  memory_append:          "🧠 Aggiornando la memoria...",
  memory_read:            "🧠 Leggendo dalla memoria...",
  memory_search:          "🧠 Cercando nella memoria...",
  memory_list:            "🧠 Elencando le note...",
  memory_index:           "🧠 Leggendo l'indice...",
  memory_lint:            "🧠 Analizzando la vault...",
  memory_ingest:          "🧠 Acquisendo la fonte...",
  check_pending_approvals:"⏳ Controllando approvazioni...",
  schedule_task:          "⏰ Programmando il task...",
  list_scheduled:         "⏰ Leggendo i task schedulati...",
  cancel_scheduled:       "⏰ Annullando il task...",
  github_repos:           "🐙 Leggendo i repository...",
  github_issues:          "🐙 Leggendo le issue...",
  github_prs:             "🐙 Leggendo le PR...",
  github_search:          "🐙 Cercando su GitHub...",
  system_stats:           "🖥️ Leggendo le statistiche...",
  drive_list:             "📁 Leggendo Google Drive...",
  drive_read:             "📁 Aprendo il file Drive...",
  sheets_read:            "📊 Leggendo il foglio...",
  sheets_write:           "📊 Scrivendo sul foglio...",
  sheets_append:          "📊 Aggiungendo righe...",
  tasks_list:             "✅ Leggendo i task...",
  tasks_create:           "✅ Creando il task...",
  tasks_complete:         "✅ Completando il task...",
  web_search:             "🔍 Cercando sul web...",
  web_fetch:              "🌐 Scaricando la pagina...",
  web_scrape:             "🌐 Estraendo dati...",
  shell_exec:             "🖥️ Eseguendo comando...",
  python_exec:            "🐍 Eseguendo codice...",
  weather:                "🌤️ Controllando il meteo...",
  stock_price:            "📈 Leggendo il prezzo...",
  rss_feed:               "📰 Leggendo il feed...",
  pdf_read:               "📄 Leggendo il PDF...",
  youtube_transcript:     "▶️ Scaricando la trascrizione...",
};

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

function TypingDots() {
  return (
    <div className="flex gap-1 items-center" style={{ padding: "4px 2px" }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: "50%",
          background: "var(--accent2)", display: "inline-block",
          animation: `dotBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
      <style>{`@keyframes dotBounce{0%,80%,100%{transform:translateY(0);opacity:.4}40%{transform:translateY(-5px);opacity:1}}`}</style>
    </div>
  );
}

const Bubble = memo(function Bubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-2.5 fade-in ${isUser ? "flex-row-reverse" : ""}`}>
      <div style={{
        background: isUser ? "var(--accent)" : "#1e1e2e",
        border: isUser ? "none" : "1px solid var(--border)",
        borderRadius: "50%", flexShrink: 0,
        width: 30, height: 30,
        display: "flex", alignItems: "center", justifyContent: "center", marginTop: 2,
      }}>
        {isUser
          ? <span style={{ color: "#fff", fontSize: 12, fontWeight: 700 }}>Tu</span>
          : <Bot size={14} color="var(--accent2)" />}
      </div>
      <div style={{ maxWidth: "78%", display: "flex", flexDirection: "column", gap: 2 }}>
        <div style={{
          background: isUser ? "var(--accent)" : "var(--surface2)",
          border: isUser ? "none" : "1px solid var(--border)",
          borderRadius: isUser ? "18px 4px 18px 18px" : "4px 18px 18px 18px",
          padding: isUser ? "9px 14px" : "12px 16px",
          wordBreak: "break-word",
        }}>
          {isUser
            ? <p style={{ color: "#fff", fontSize: 13.5, lineHeight: 1.6, margin: 0 }}>{msg.content}</p>
            : <ReactMarkdown components={MD}>{msg.content}</ReactMarkdown>}
        </div>
      </div>
    </div>
  );
});

function StreamingBubble({ content, toolStatus }: { content: string; toolStatus: string }) {
  return (
    <div className="flex gap-2.5 fade-in">
      <div style={{
        background: "#1e1e2e", border: "1px solid var(--border)",
        borderRadius: "50%", flexShrink: 0,
        width: 30, height: 30,
        display: "flex", alignItems: "center", justifyContent: "center", marginTop: 2,
      }}>
        <Bot size={14} color="var(--accent2)" />
      </div>
      <div style={{ maxWidth: "78%" }}>
        {toolStatus && (
          <p className="shimmer-text" style={{ fontSize: 11, marginBottom: 6, fontFamily: "monospace" }}>
            {toolStatus}
          </p>
        )}
        {content ? (
          <div style={{
            background: "var(--surface2)", border: "1px solid var(--border)",
            borderRadius: "4px 18px 18px 18px", padding: "12px 16px", wordBreak: "break-word",
          }}>
            <ReactMarkdown components={MD}>{content}</ReactMarkdown>
            <span className="stream-cursor" />
          </div>
        ) : !toolStatus ? (
          <div style={{ background: "var(--surface2)", border: "1px solid var(--border)", borderRadius: "4px 18px 18px 18px", padding: "10px 16px" }}>
            <TypingDots />
          </div>
        ) : null}
      </div>
    </div>
  );
}

const SUGGESTIONS = [
  { icon: Mail,     text: "Controlla le email non lette" },
  { icon: Calendar, text: "Cosa ho in calendario oggi?" },
  { icon: FileText, text: "Riassumi le ultime 5 email" },
  { icon: Sparkles, text: "Cosa sai di me?" },
];

let _currentAudio: HTMLAudioElement | null = null;

function cancelTts() {
  if (_currentAudio) {
    _currentAudio.pause();
    _currentAudio.src = "";
    _currentAudio = null;
  }
}

async function tts(text: string, onStart: () => void, onEnd: () => void) {
  cancelTts();
  try {
    const resp = await fetch("http://localhost:8080/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!resp.ok) { onEnd(); return; }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    _currentAudio = audio;
    audio.onended = () => { URL.revokeObjectURL(url); _currentAudio = null; onEnd(); };
    audio.onerror = () => { URL.revokeObjectURL(url); _currentAudio = null; onEnd(); };
    onStart();
    audio.play().catch(onEnd);
  } catch {
    onEnd();
  }
}

type Props = {
  injectedMessage?: string;
  onInjectedConsumed?: () => void;
};

export default function Chat({ injectedMessage, onInjectedConsumed }: Props) {
  const [messages,         setMessages]         = useState<Message[]>([]);
  const [input,            setInput]            = useState("");
  const [loading,          setLoading]          = useState(false);
  const [pending,          setPending]          = useState<PendingAction[]>([]);
  const [focused,          setFocused]          = useState(false);
  const [ttsEnabled,       setTtsEnabled]       = useState(true);
  const [avatarState,      setAvatarState]      = useState<AvatarState>("idle");
  const [streamingContent, setStreamingContent] = useState("");
  const [toolStatus,       setToolStatus]       = useState("");
  const [isListening,      setIsListening]      = useState(false);
  const [hasStt,           setHasStt]           = useState(false);

  const bottomRef    = useRef<HTMLDivElement>(null);
  const inputRef     = useRef<HTMLTextAreaElement>(null);
  const recognRef    = useRef<any>(null);

  // detect STT support
  useEffect(() => {
    setHasStt(typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window));
  }, []);

  // load history + pending
  async function loadHistory() { try { setMessages((await api.getHistory()).messages); } catch {} }
  async function loadPending() { try { setPending((await api.getPending()).pending); } catch {} }

  useEffect(() => {
    loadHistory();
    loadPending();
    const t = setInterval(loadPending, 10_000);
    return () => clearInterval(t);
  }, []);

  // injected message from sidebar
  useEffect(() => {
    if (!injectedMessage) return;
    setInput(injectedMessage);
    onInjectedConsumed?.();
    setTimeout(() => inputRef.current?.focus(), 50);
  }, [injectedMessage, onInjectedConsumed]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, loading]);

  const autoResize = useCallback((el: HTMLTextAreaElement) => {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, []);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", content: text.trim() }]);
    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
    setLoading(true);
    setAvatarState("thinking");
    setStreamingContent("");
    setToolStatus("");

    let reply = "";

    try {
      const stream = api.streamTask(text.trim());
      for await (const ev of stream) {
        if (ev.event === "status") {
          if (ev.data.phase === "thinking")   setAvatarState("thinking");
          if (ev.data.phase === "responding") { setAvatarState("speaking"); setToolStatus(""); }
        } else if (ev.event === "tool") {
          setToolStatus(TOOL_LABELS[ev.data.name] ?? `⚙️ ${ev.data.name}...`);
          setAvatarState("thinking");
        } else if (ev.event === "token") {
          setStreamingContent((s) => s + ev.data.text);
        } else if (ev.event === "done") {
          reply = ev.data.reply;
        }
      }
    } catch {
      // fallback to non-streaming
      try {
        const res = await api.sendTask(text.trim());
        reply = res.reply;
      } catch {
        reply = "⚠️ Impossibile contattare il backend.";
      }
    }

    setStreamingContent("");
    setToolStatus("");
    setMessages((m) => [...m, { role: "assistant", content: reply }]);
    await loadPending();

    if (ttsEnabled && reply) {
      tts(reply, () => setAvatarState("speaking"), () => setAvatarState("idle"));
    } else {
      setAvatarState("idle");
    }

    setLoading(false);
    setTimeout(() => inputRef.current?.focus(), 50);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
  }

  function startListening() {
    if (!hasStt) return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = "it-IT";
    rec.continuous = false;
    rec.interimResults = true;
    rec.onresult = (e: any) => {
      const transcript = Array.from(e.results as any[]).map((r: any) => r[0].transcript).join("");
      setInput(transcript);
      if (inputRef.current) autoResize(inputRef.current);
    };
    rec.onend  = () => setIsListening(false);
    rec.onerror = () => setIsListening(false);
    rec.start();
    recognRef.current = rec;
    setIsListening(true);
  }

  function stopListening() { recognRef.current?.stop(); setIsListening(false); }
  function toggleMic() { isListening ? stopListening() : startListening(); }

  const canSend = input.trim().length > 0 && !loading;
  const showEmpty = messages.length === 0 && !loading && !streamingContent;

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">
      <PendingBanner actions={pending} onResolved={loadPending} />

      {/* messages */}
      <div className="flex-1 overflow-y-auto px-5 py-5" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {showEmpty && (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <JarvisAvatar state={avatarState} size={100} />
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
                    background: "var(--surface2)", border: "1px solid var(--border)",
                    borderRadius: 12, padding: "10px 12px",
                    color: "var(--text)", textAlign: "left",
                    transition: "border-color 0.15s, background 0.15s",
                    display: "flex", flexDirection: "column", gap: 6,
                  }}
                  onMouseEnter={(e) => { (e.currentTarget).style.borderColor = "var(--accent)"; (e.currentTarget).style.background = "var(--surface)"; }}
                  onMouseLeave={(e) => { (e.currentTarget).style.borderColor = "var(--border)"; (e.currentTarget).style.background = "var(--surface2)"; }}
                >
                  <Icon size={14} color="var(--accent2)" />
                  <span style={{ fontSize: 12, lineHeight: 1.4 }}>{text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => <Bubble key={i} msg={m} />)}

        {(loading || streamingContent || toolStatus) && (
          <StreamingBubble content={streamingContent} toolStatus={toolStatus} />
        )}

        <div ref={bottomRef} />
      </div>

      {/* avatar + TTS bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "8px 16px 20px", gap: 16, background: "var(--surface)" }}>
        <JarvisAvatar state={avatarState} size={64} />
        <button
          onClick={() => { if (ttsEnabled) cancelTts(); setTtsEnabled((v) => !v); if (avatarState === "speaking") setAvatarState("idle"); }}
          title={ttsEnabled ? "Disattiva voce" : "Attiva voce"}
          style={{ background: "none", border: "none", cursor: "pointer", color: ttsEnabled ? "var(--accent2)" : "var(--muted)", padding: 4 }}
        >
          {ttsEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
        </button>
      </div>

      {/* input */}
      <div style={{ background: "var(--surface)", padding: "8px 16px 14px" }}>
        <div style={{
          background: "var(--surface2)",
          border: `1px solid ${focused ? "var(--accent)" : "var(--border)"}`,
          borderRadius: 16, display: "flex", alignItems: "flex-end", gap: 8,
          padding: "10px 10px 10px 16px", transition: "border-color 0.15s",
        }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); autoResize(e.target); }}
            onKeyDown={onKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Scrivi un messaggio…"
            rows={1}
            style={{
              background: "transparent", border: "none", outline: "none",
              color: "var(--text)", fontSize: "13.5px", lineHeight: "1.6",
              resize: "none", flex: 1, minHeight: 24, maxHeight: 200,
              overflowY: "auto", fontFamily: "inherit", padding: 0,
            }}
            autoFocus
          />
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4, flexShrink: 0 }}>
            {hasStt && (
              <button
                onClick={toggleMic}
                title={isListening ? "Ferma ascolto" : "Parla"}
                className={isListening ? "mic-active" : ""}
                style={{
                  background: isListening ? "var(--accent2)" : "var(--surface)",
                  border: `1px solid ${isListening ? "var(--accent2)" : "var(--border)"}`,
                  borderRadius: 10, width: 34, height: 34,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  cursor: "pointer", transition: "background 0.15s",
                }}
              >
                {isListening ? <MicOff size={14} color="#fff" /> : <Mic size={14} color="var(--muted)" />}
              </button>
            )}
            <button
              onClick={() => send(input)}
              disabled={!canSend}
              style={{
                background: canSend ? "var(--accent)" : "var(--border)",
                borderRadius: 10, width: 34, height: 34,
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.15s, transform 0.1s",
                cursor: canSend ? "pointer" : "default", border: "none",
              }}
              onMouseDown={(e) => canSend && ((e.currentTarget).style.transform = "scale(0.92)")}
              onMouseUp={(e) => ((e.currentTarget).style.transform = "scale(1)")}
            >
              <Send size={14} color="#fff" />
            </button>
          </div>
        </div>
        <p style={{ color: "var(--muted)", fontSize: 11, textAlign: "center", marginTop: 6 }}>
          Enter per inviare · Shift+Enter per andare a capo{hasStt ? " · 🎙 per dettare" : ""}
        </p>
      </div>
    </div>
  );
}
