"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { GitBranch, BarChart2 } from "lucide-react";

const LINKS = [
  { href: "/graph", label: "MEMORIA", icon: GitBranch },
  { href: "/stats", label: "STATS", icon: BarChart2 },
];

export default function Nav() {
  const path = usePathname();
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
            v1.0 // ONLINE
          </div>
        </div>
      </Link>

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
          }}>
            <Icon size={12} />
            {label}
          </Link>
        );
      })}
    </header>
  );
}
