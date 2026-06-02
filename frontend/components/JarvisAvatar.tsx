"use client";

export type AvatarState = "idle" | "thinking" | "speaking";

const COLORS = {
  idle:     { primary: "#00f0ff", secondary: "#0066ff", glow: "#00f0ff44" },
  thinking: { primary: "#ff006e", secondary: "#aa00ff", glow: "#ff006e44" },
  speaking: { primary: "#00ff9d", secondary: "#00aaff", glow: "#00ff9d44" },
};

export default function JarvisAvatar({ state }: { state: AvatarState }) {
  const c = COLORS[state];

  return (
    <div style={{ position: "relative", width: 80, height: 80, flexShrink: 0 }}>
      <style>{`
        @keyframes scanline {
          0%   { top: 10%; opacity: 1; }
          100% { top: 90%; opacity: 0; }
        }
        @keyframes rotate-ring {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes rotate-ring-rev {
          from { transform: rotate(0deg); }
          to   { transform: rotate(-360deg); }
        }
        @keyframes glitch-h {
          0%,100% { clip-path: inset(0 0 98% 0); transform: translate(-2px,0); }
          20%     { clip-path: inset(30% 0 50% 0); transform: translate(2px,0); }
          40%     { clip-path: inset(60% 0 20% 0); transform: translate(-1px,0); }
          60%     { clip-path: inset(80% 0 5%  0); transform: translate(1px,0); }
          80%     { clip-path: inset(10% 0 70% 0); transform: translate(-2px,0); }
        }
        @keyframes core-pulse {
          0%,100% { opacity: 0.85; }
          50%     { opacity: 1; }
        }
        @keyframes bar-wave {
          0%,100% { transform: scaleY(0.3); }
          50%     { transform: scaleY(1); }
        }
        @keyframes blink-dot {
          0%,100% { opacity: 1; }
          50%     { opacity: 0; }
        }
        @keyframes hud-spin {
          from { stroke-dashoffset: 0; }
          to   { stroke-dashoffset: -251; }
        }
      `}</style>

      {/* outer glow */}
      <div style={{
        position: "absolute", inset: -6,
        borderRadius: "50%",
        background: `radial-gradient(circle, ${c.glow} 0%, transparent 70%)`,
        transition: "background 0.4s",
      }} />

      {/* SVG rings */}
      <svg viewBox="0 0 80 80" width="80" height="80" style={{ position: "absolute", inset: 0 }}>
        {/* outer dashed ring — rotates */}
        <circle cx="40" cy="40" r="37"
          fill="none"
          stroke={c.primary}
          strokeWidth="1"
          strokeDasharray="4 3"
          strokeOpacity="0.6"
          style={{ transformOrigin: "40px 40px", animation: `rotate-ring ${state === "idle" ? "6s" : "1.5s"} linear infinite` }}
        />
        {/* inner dashed ring — counter-rotates */}
        <circle cx="40" cy="40" r="30"
          fill="none"
          stroke={c.secondary}
          strokeWidth="1"
          strokeDasharray="2 5"
          strokeOpacity="0.5"
          style={{ transformOrigin: "40px 40px", animation: `rotate-ring-rev ${state === "idle" ? "8s" : "2s"} linear infinite` }}
        />
        {/* progress arc */}
        <circle cx="40" cy="40" r="34"
          fill="none"
          stroke={c.primary}
          strokeWidth="2"
          strokeDasharray={state === "thinking" ? "40 174" : state === "speaking" ? "130 44" : "70 114"}
          strokeLinecap="round"
          strokeOpacity="0.9"
          transform="rotate(-90 40 40)"
          style={{ transition: "stroke-dasharray 0.3s, stroke 0.4s", filter: `drop-shadow(0 0 3px ${c.primary})` }}
        />
        {/* corner notches */}
        {[0, 90, 180, 270].map((deg) => (
          <rect key={deg} x="38.5" y="2" width="3" height="6" fill={c.primary} opacity="0.9"
            style={{ transformOrigin: "40px 40px", transform: `rotate(${deg}deg)`, filter: `drop-shadow(0 0 2px ${c.primary})` }}
          />
        ))}
        {/* scanline */}
        {state !== "idle" && (
          <line x1="14" y1="40" x2="66" y2="40"
            stroke={c.primary} strokeWidth="1" strokeOpacity="0.7"
            style={{ animation: "scanline 0.8s linear infinite", transformOrigin: "40px 40px" }}
          />
        )}
      </svg>

      {/* core */}
      <div style={{
        position: "absolute", inset: 14,
        borderRadius: "50%",
        background: `radial-gradient(circle at 38% 35%, ${c.secondary}33, #080810 70%)`,
        border: `1px solid ${c.primary}55`,
        display: "flex", alignItems: "center", justifyContent: "center",
        animation: "core-pulse 2s ease-in-out infinite",
        overflow: "hidden",
      }}>

        {/* glitch overlay (speaking) */}
        {state === "speaking" && (
          <>
            <div style={{ position: "absolute", inset: 0, background: `${c.primary}11`, animation: "glitch-h 0.15s steps(1) infinite" }} />
            <div style={{ position: "absolute", inset: 0, background: `${c.secondary}11`, animation: "glitch-h 0.2s steps(1) 0.07s infinite" }} />
          </>
        )}

        {/* waveform (speaking) */}
        {state === "speaking" ? (
          <div style={{ display: "flex", gap: 2.5, alignItems: "center", height: 18 }}>
            {[0.15, 0.3, 0.1, 0.25, 0.05, 0.2, 0.1].map((delay, i) => (
              <div key={i} style={{
                width: 2, height: "100%",
                background: `linear-gradient(to top, ${c.secondary}, ${c.primary})`,
                borderRadius: 1,
                boxShadow: `0 0 4px ${c.primary}`,
                transformOrigin: "center",
                animation: `bar-wave 0.4s ${delay}s ease-in-out infinite`,
              }} />
            ))}
          </div>
        ) : state === "thinking" ? (
          /* rotating triangle / spinner */
          <svg viewBox="0 0 24 24" width="18" height="18" style={{ animation: "rotate-ring 0.6s linear infinite" }}>
            <circle cx="12" cy="4" r="2" fill={c.primary} />
            <circle cx="20" cy="18" r="2" fill={c.secondary} opacity="0.6" />
            <circle cx="4" cy="18" r="2" fill={c.primary} opacity="0.3" />
          </svg>
        ) : (
          /* idle: blinking cursor */
          <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
            <span style={{ color: c.primary, fontSize: 9, fontFamily: "monospace", letterSpacing: 1 }}>SYS</span>
            <div style={{ width: 6, height: 10, background: c.primary, animation: "blink-dot 1s step-end infinite", boxShadow: `0 0 4px ${c.primary}` }} />
          </div>
        )}
      </div>

      {/* status label */}
      <div style={{
        position: "absolute", bottom: -18, left: "50%", transform: "translateX(-50%)",
        fontSize: 8, fontFamily: "monospace", letterSpacing: 2,
        color: c.primary, opacity: 0.8, whiteSpace: "nowrap",
        textShadow: `0 0 6px ${c.primary}`,
        transition: "color 0.3s",
      }}>
        {state === "idle" ? "SYS:ONLINE" : state === "thinking" ? "PROC:DATA" : "TX:AUDIO"}
      </div>
    </div>
  );
}
