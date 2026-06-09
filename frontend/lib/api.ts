const BASE   = process.env.NEXT_PUBLIC_API_URL    ?? "http://localhost:8080";
const SECRET = process.env.NEXT_PUBLIC_API_SECRET ?? "";

export type Message = { role: "user" | "assistant"; content: string };
export type Email = { id: string; from: string; subject: string; date: string; snippet: string };
export type EmailDetail = { id: string; from: string; to: string; subject: string; date: string; body: string };
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

export type Persona = { slug: string; name: string; description: string; emoji: string; active?: boolean };

export type SSEEvent =
  | { event: "status";   data: { phase: "thinking" | "responding" } }
  | { event: "tool";     data: { name: string } }
  | { event: "token";    data: { text: string } }
  | { event: "done";     data: { reply: string } }
  | { event: "error";    data: { message: string } };

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  return { ...(SECRET ? { "X-Secret": SECRET } : {}), ...extra };
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function* streamTask(task: string): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${BASE}/task/stream`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ task }),
  });
  if (!res.ok || !res.body) throw new Error(`${res.status} /task/stream`);

  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    let eventName = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        eventName = line.slice(7).trim();
      } else if (line.startsWith("data: ") && eventName) {
        try {
          const data = JSON.parse(line.slice(6));
          yield { event: eventName, data } as SSEEvent;
        } catch {}
        eventName = "";
      }
    }
  }
}

async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`, { cache: "no-store", signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

export const api = {
  sendTask: (task: string) =>
    post<{ reply: string; pending_approvals: number }>("/task", { task }),

  streamTask,

  checkHealth,

  getHistory: () =>
    get<{ messages: Message[] }>("/history"),

  getEmails: () =>
    get<{ emails: Email[] }>("/emails?max_results=8"),

  getEmail: (id: string) =>
    get<EmailDetail>(`/email/${id}`),

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

  getPersonas: () =>
    get<{ personas: Persona[]; active: string }>("/personas"),

  getActivePersona: () =>
    get<Persona>("/persona"),

  setPersona: (slug: string) =>
    post<Persona>(`/persona/${slug}`, {}),
};
