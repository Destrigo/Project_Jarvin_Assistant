"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, MessageSquare, GitBranch, BarChart2 } from "lucide-react";

const LINKS = [
  { href: "/", label: "Chat", icon: MessageSquare },
  { href: "/graph", label: "Grafo", icon: GitBranch },
  { href: "/stats", label: "Stats", icon: BarChart2 },
];

export default function Nav() {
  const path = usePathname();
  return (
    <header
      style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)", height: 49 }}
      className="flex items-center gap-4 px-4 shrink-0"
    >
      <div className="flex items-center gap-2 mr-4">
        <div style={{ background: "var(--accent)", borderRadius: 8, padding: 5 }}>
          <Bot size={16} color="#fff" />
        </div>
        <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>Jarvis</span>
      </div>

      {LINKS.map(({ href, label, icon: Icon }) => {
        const active = path === href;
        return (
          <Link
            key={href}
            href={href}
            style={{
              color: active ? "var(--accent2)" : "var(--muted)",
              borderBottom: active ? "2px solid var(--accent2)" : "2px solid transparent",
              paddingBottom: 2,
              fontSize: 13,
              fontWeight: active ? 600 : 400,
              display: "flex",
              alignItems: "center",
              gap: 6,
              height: "100%",
              transition: "color 0.15s",
            }}
          >
            <Icon size={14} />
            {label}
          </Link>
        );
      })}
    </header>
  );
}
