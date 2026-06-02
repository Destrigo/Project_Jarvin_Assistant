const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

export type Message = { role: "user" | "assistant"; content: string };
export type Email = { id: string; from: string; subject: string; date: string; snippet: string };
export type CalEvent = { id: string; title: string; start: string; end: string; description: string };
export type PendingAction = { id: string; type: string; description: string; status: string; created_at: string };
export type GraphNode = { id: number; name: string; path: string; folder: string; size: number };
export type GraphLink = { source: number; target: number };
export type GraphData = { nodes: GraphNode[]; links: GraphLink[] };
export type Stats = {
  vault: { total_notes: number; memory_notes: number; conversation_notes: number };
  conversations: { total_messages: number; user_messages: number };
  approvals: { pending: number; resolved: number };
};

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

export const api = {
  sendTask: (task: string) =>
    post<{ reply: string; pending_approvals: number }>("/task", { task }),

  getHistory: () =>
    get<{ messages: Message[] }>("/history"),

  getEmails: () =>
    get<{ emails: Email[] }>("/emails?max_results=8"),

  getEvents: () =>
    get<{ events: CalEvent[] }>("/events?days_ahead=7"),

  getPending: () =>
    get<{ pending: PendingAction[] }>("/pending"),

  resolve: (id: string, status: "approved" | "skipped") =>
    post<{ status: string; result?: string }>(`/resolve/${id}?status=${status}`, {}),

  getMemoryGraph: () =>
    get<GraphData>("/memory/graph"),

  getNote: (title: string) =>
    get<{ title: string; content: string; path: string; folder: string }>(`/memory/note?title=${encodeURIComponent(title)}`),

  getStats: () =>
    get<Stats>("/stats"),
};
