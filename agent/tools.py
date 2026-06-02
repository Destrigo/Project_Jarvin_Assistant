"""Tool registry: schema definitions + callable implementations.

READ operations  → execute immediately (autonomous)
WRITE operations → queue for Telegram approval, return pending status
"""
import json
from pathlib import Path

import memory.store as store
from integrations.telegram import send_approval_request


# ── helpers ───────────────────────────────────────────────────────────────────

def _queue(action_type: str, description: str, payload: dict) -> dict:
    action_id = store.queue_action(action_type, description, payload)
    send_approval_request(action_id, description)
    return {"status": "pending_approval", "action_id": action_id,
            "message": f"Richiesta inviata su Telegram per approvazione (id: {action_id})"}


# ── tool implementations ───────────────────────────────────────────────────────

def list_emails(max_results: int = 10, query: str = "is:unread") -> dict:
    from integrations.gmail import list_emails as _list
    return {"emails": _list(max_results=max_results, query=query)}


def read_email(email_id: str) -> dict:
    from integrations.gmail import read_email as _read
    return _read(email_id)


def send_email(to: str, subject: str, body: str) -> dict:
    desc = f"📧 *Invia email*\nA: `{to}`\nOggetto: _{subject}_\n\n{body[:300]}"
    return _queue("send_email", desc, {"to": to, "subject": subject, "body": body})


def list_events(days_ahead: int = 7) -> dict:
    from integrations.calendar import list_events as _list
    return {"events": _list(days_ahead=days_ahead)}


def create_event(title: str, start: str, end: str,
                 description: str = "", attendees: list[str] | None = None) -> dict:
    atts = ", ".join(attendees) if attendees else "nessuno"
    desc = f"📅 *Crea evento*\nTitolo: _{title}_\n{start} → {end}\nPartecipanti: {atts}"
    return _queue("create_event", desc,
                  {"title": title, "start": start, "end": end,
                   "description": description, "attendees": attendees or []})


def read_file(path: str) -> dict:
    p = Path(path).expanduser()
    if not p.exists():
        return {"error": f"File non trovato: {path}"}
    return {"path": str(p), "content": p.read_text()[:4000]}


def write_file(path: str, content: str) -> dict:
    desc = f"📝 *Scrivi file*\nPath: `{path}`\n\n```\n{content[:300]}\n```"
    return _queue("write_file", desc, {"path": path, "content": content})


def list_files(directory: str = ".") -> dict:
    p = Path(directory).expanduser()
    if not p.is_dir():
        return {"error": f"Directory non trovata: {directory}"}
    files = [str(f.relative_to(p)) for f in p.iterdir()]
    return {"directory": str(p), "files": files}


def check_pending_approvals() -> dict:
    pending = store.pending_actions()
    return {"pending": pending, "count": len(pending)}


# ── Obsidian memory ───────────────────────────────────────────────────────────

def memory_write(title: str, content: str, folder: str = "") -> dict:
    from integrations.obsidian import write_note
    return write_note(title, content, folder)


def memory_append(title: str, content: str, folder: str = "") -> dict:
    from integrations.obsidian import append_to_note
    return append_to_note(title, content, folder)


def memory_read(title: str, folder: str = "") -> dict:
    from integrations.obsidian import read_note
    return read_note(title, folder)


def memory_search(query: str) -> dict:
    from integrations.obsidian import search_notes
    return search_notes(query)


def memory_list(folder: str = "") -> dict:
    from integrations.obsidian import list_notes
    return list_notes(folder)


# ── schema + dispatch ──────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_emails",
            "description": "Elenca le email nella inbox. Di default mostra le non lette.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "default": 10},
                    "query": {"type": "string", "default": "is:unread",
                              "description": "Query Gmail es. 'is:unread from:boss@co.com'"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": "Legge il testo completo di un'email dato il suo ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {"type": "string"},
                },
                "required": ["email_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Prepara e invia un'email (richiede approvazione su Telegram).",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": "Elenca gli eventi del calendario Google nei prossimi N giorni.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {"type": "integer", "default": 7},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Crea un evento nel calendario (richiede approvazione su Telegram).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start": {"type": "string", "description": "ISO 8601, es. 2025-06-10T14:00:00+02:00"},
                    "end": {"type": "string"},
                    "description": {"type": "string", "default": ""},
                    "attendees": {"type": "array", "items": {"type": "string"}, "default": []},
                },
                "required": ["title", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Legge il contenuto di un file locale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Scrive o sovrascrive un file locale (richiede approvazione su Telegram).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Elenca i file in una directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "default": "."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_pending_approvals",
            "description": "Mostra le azioni in attesa di approvazione su Telegram.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_write",
            "description": "Salva una nota nella vault Obsidian (crea o sovrascrive).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "folder": {"type": "string", "default": ""},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_append",
            "description": "Aggiunge contenuto a una nota esistente (o la crea).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "folder": {"type": "string", "default": ""},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_read",
            "description": "Legge una nota dalla vault Obsidian.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "folder": {"type": "string", "default": ""},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "Cerca testo in tutte le note della vault Obsidian.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_list",
            "description": "Elenca tutte le note nella vault (o in una sottocartella).",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "default": ""},
                },
            },
        },
    },
]

_DISPATCH: dict[str, callable] = {
    "list_emails": list_emails,
    "read_email": read_email,
    "send_email": send_email,
    "list_events": list_events,
    "create_event": create_event,
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "check_pending_approvals": check_pending_approvals,
    "memory_write": memory_write,
    "memory_append": memory_append,
    "memory_read": memory_read,
    "memory_search": memory_search,
    "memory_list": memory_list,
}


def execute(name: str, args: dict) -> str:
    fn = _DISPATCH.get(name)
    if fn is None:
        return json.dumps({"error": f"Tool sconosciuto: {name}"})
    try:
        result = fn(**args)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
