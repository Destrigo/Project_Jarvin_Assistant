"use client";

export type AvatarState = "idle" | "thinking" | "speaking";

export default function JarvisAvatar({ state }: { state: AvatarState }) {
  const color = state === "thinking" ? "#f59e0b" : state === "speaking" ? "#34d399" : "#6c63ff";
  const speed = state === "idle" ? "3s" : state === "thinking" ? "0.8s" : "0.5s";

  return (
    <div style={{ position: "relative", width: 72, height: 72, flexShrink: 0 }}>
      <style>{`
        @keyframes ripple {
          0%   { transform: scale(1);   opacity: 0.6; }
          100% { transform: scale(1.9); opacity: 0; }
        }
        @keyframes breathe {
          0%, 100% { transform: scale(1);    opacity: 0.15; }
          50%       { transform: scale(1.35); opacity: 0.35; }
        }
        @keyframes corePulse {
          0%, 100% { transform: scale(1); }
          50%       { transform: scale(${state === "speaking" ? "1.08" : "1.03"}); }
        }
        @keyframes wave {
          0%        { transform: scaleY(0.4); }
          25%       { transform: scaleY(1); }
          50%       { transform: scaleY(0.4); }
          75%       { transform: scaleY(0.9); }
          100%      { transform: scaleY(0.4); }
        }
      `}</style>

      {/* ripple rings */}
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            border: `1.5px solid ${color}`,
            animation: state !== "idle"
              ? `ripple ${speed} ${i * 0.22}s ease-out infinite`
              : `breathe 3s ${i * 0.6}s ease-in-out infinite`,
          }}
        />
      ))}

      {/* core circle */}
      <div
        style={{
          position: "absolute",
          inset: 14,
          borderRadius: "50%",
          background: `radial-gradient(circle at 38% 38%, ${color}cc, ${color}55)`,
          boxShadow: `0 0 18px ${color}66`,
          animation: `corePulse ${speed} ease-in-out infinite`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        {/* waveform bars when speaking */}
        {state === "speaking" && (
          <div style={{ display: "flex", gap: 2, alignItems: "center", height: 18 }}>
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                style={{
                  width: 2.5,
                  height: "100%",
                  background: "#fff",
                  borderRadius: 2,
                  transformOrigin: "center",
                  animation: `wave 0.5s ${i * 0.08}s ease-in-out infinite`,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
