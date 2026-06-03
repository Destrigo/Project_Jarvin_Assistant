"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { GitBranch, BarChart2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const LINKS = [
  { href: "/graph", label: "MEMORIA", icon: GitBranch },
  { href: "/stats", label: "STATS",   icon: BarChart2 },
];

export default function Nav() {
  const path = usePathname();
  const [pending, setPending]   = useState(0);
  const [online,  setOnline]    = useState<boolean | null>(null);

  useEffect(() => {
    async function tick() {
      const [healthy, pend] = await Promise.all([
        api.checkHealth(),
        api.getPending().then((r) => r.pending.length).catch(() => 0),
      ]);
      setOnline(healthy);
      setPending(pend);
    }
    tick();
    const t = setInterval(tick, 15_000);
    return () => clearInterval(t);
  }, []);

  return (
    <header style={{
      background: "var(--surface)",
      borderBottom: "1px solid var(--border)",
      boxShadow: "0 1px 0 #00f0ff22",
      height: 49,
      display: "flex",
      alignItems: "center",
      gap: 24,
      padding: "0 16px",
      flexShrink: 0,
    }}>
      {/* logo */}
      <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", marginRight: 8 }}>
        <div style={{
          width: 28, height: 28,
          border: "1px solid var(--accent)",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 0 8px var(--accent), inset 0 0 8px #00f0ff11",
          clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
          background: "#00f0ff11",
        }}>
          <span style={{ color: "var(--accent)", fontSize: 10, fontFamily: "monospace", fontWeight: 700 }}>J</span>
        </div>
        <div>
          <div style={{ color: "var(--accent)", fontSize: 12, fontWeight: 700, letterSpacing: 3, lineHeight: 1, textShadow: "0 0 8px var(--accent)" }}>
            JARVIS
          </div>
          <div style={{ color: "var(--muted)", fontSize: 8, letterSpacing: 2, lineHeight: 1.2 }}>
            v1.0 // {online === null ? "..." : online ? "ONLINE" : "OFFLINE"}
          </div>
        </div>
      </Link>

      {/* connection dot */}
      <div
        title={online === null ? "Connessione..." : online ? "Backend online" : "Backend offline"}
        style={{
          width: 7, height: 7, borderRadius: "50%",
          background: online === null ? "var(--muted)" : online ? "var(--green)" : "var(--red)",
          boxShadow: online ? "0 0 6px var(--green)" : online === false ? "0 0 6px var(--red)" : "none",
          flexShrink: 0,
          marginLeft: -16,
          transition: "background 0.3s, box-shadow 0.3s",
        }}
      />

      <div style={{ flex: 1 }} />

      {LINKS.map(({ href, label, icon: Icon }) => {
        const active = path === href;
        return (
          <Link key={href} href={href} style={{
            color: active ? "var(--accent)" : "var(--muted)",
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: 2,
            display: "flex",
            alignItems: "center",
            gap: 6,
            height: "100%",
            textDecoration: "none",
            borderBottom: active ? "2px solid var(--accent)" : "2px solid transparent",
            textShadow: active ? "0 0 6px var(--accent)" : "none",
            transition: "color 0.15s, text-shadow 0.15s",
            position: "relative",
          }}>
            <Icon size={12} />
            {label}
            {/* pending badge — shown only on non-chat pages or always */}
            {label === "STATS" && pending > 0 && (
              <span style={{
                position: "absolute", top: 10, right: -8,
                background: "var(--accent2)",
                color: "#fff",
                fontSize: 8, fontWeight: 700,
                borderRadius: "50%",
                width: 14, height: 14,
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: "0 0 6px var(--accent2)",
              }}>
                {pending > 9 ? "9+" : pending}
              </span>
            )}
          </Link>
        );
      })}

      {/* global pending indicator in nav */}
      {pending > 0 && (
        <div style={{
          display: "flex", alignItems: "center", gap: 5,
          background: "#1a1520",
          border: "1px solid var(--accent2)",
          borderRadius: 6,
          padding: "3px 8px",
        }}>
          <div style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--accent2)", boxShadow: "0 0 4px var(--accent2)" }} />
          <span style={{ color: "var(--accent2)", fontSize: 9, fontWeight: 700, letterSpacing: 1 }}>
            {pending} IN ATTESA
          </span>
        </div>
      )}
    </header>
  );
}
