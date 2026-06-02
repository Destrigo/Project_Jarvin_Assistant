const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

export type Message = { role: "user" | "assistant"; content: string };
export type Email = { id: string; from: string; subject: string; date: string; snippet: string };
export type CalEvent = { id: string; title: string; start: string; end: string; description: string };
export type PendingAction = { id: string; type: string; description: string; status: string; created_at: string };

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
};
