// Jarvis offline. Per riattivare: git revert HEAD && git push
export default function Home() {
  return (
    <div style={{
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      height: "100%", gap: "12px", color: "#888",
      fontFamily: "monospace",
    }}>
      <span style={{ fontSize: "2rem" }}>⚫</span>
      <span style={{ fontSize: "1.1rem" }}>Jarvis offline</span>
    </div>
  );
}
