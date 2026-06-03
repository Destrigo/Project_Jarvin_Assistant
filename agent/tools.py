"""Tool registry: schema definitions + callable implementations.

READ operations  → execute immediately (autonomous)
WRITE operations → queue for Telegram approval, return pending status
"""
import json
import subprocess
import tempfile
from pathlib import Path

import memory.store as store
from integrations.telegram import send_approval_request

_SHELL_DANGEROUS = ["rm ", "sudo ", "kill ", "pkill ", "dd ", "mkfs", "fdisk",
                    "> /dev/", "chmod 777", ":(){ :|:& };", "shutdown", "reboot"]


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


# ── Scheduler ─────────────────────────────────────────────────────────────────

def schedule_task(task: str, when: str, note: str = "") -> dict:
    from integrations.scheduler import schedule_task as _st
    return _st(task, when, note)


def list_scheduled(include_done: bool = False) -> dict:
    from integrations.scheduler import list_scheduled as _ls
    return _ls(include_done)


def cancel_scheduled(task_id: str) -> dict:
    from integrations.scheduler import cancel_scheduled as _cs
    return _cs(task_id)


# ── GitHub ────────────────────────────────────────────────────────────────────

def github_repos(user: str = "", max_results: int = 10) -> dict:
    from integrations.github_client import github_repos as _gr
    return _gr(user, max_results)


def github_issues(repo: str, state: str = "open", max_results: int = 10) -> dict:
    from integrations.github_client import github_issues as _gi
    return _gi(repo, state, max_results)


def github_prs(repo: str, state: str = "open", max_results: int = 10) -> dict:
    from integrations.github_client import github_prs as _gp
    return _gp(repo, state, max_results)


def github_search(query: str, kind: str = "repositories", max_results: int = 8) -> dict:
    from integrations.github_client import github_search as _gs
    return _gs(query, kind, max_results)


# ── System stats ──────────────────────────────────────────────────────────────

def system_stats() -> dict:
    from integrations.system_stats import system_stats as _ss
    return _ss()


# ── Google Drive ──────────────────────────────────────────────────────────────

def drive_list(folder_id: str = "root", max_results: int = 20, query: str = "") -> dict:
    from integrations.gdrive import drive_list as _dl
    return _dl(folder_id, max_results, query)


def drive_read(file_id: str) -> dict:
    from integrations.gdrive import drive_read as _dr
    return _dr(file_id)


# ── Google Sheets ─────────────────────────────────────────────────────────────

def sheets_read(spreadsheet_id: str, range_: str = "Sheet1") -> dict:
    from integrations.gsheets import sheets_read as _sr
    return _sr(spreadsheet_id, range_)


def sheets_write(spreadsheet_id: str, range_: str, values: list) -> dict:
    rows_preview = str(values)[:200]
    desc = f"📊 *Scrivi su Google Sheets*\nSheet: `{spreadsheet_id}`\nRange: `{range_}`\nDati:\n```\n{rows_preview}\n```"
    return _queue("sheets_write", desc, {"spreadsheet_id": spreadsheet_id, "range_": range_, "values": values})


def sheets_append(spreadsheet_id: str, range_: str, values: list) -> dict:
    rows_preview = str(values)[:200]
    desc = f"📊 *Aggiungi righe su Google Sheets*\nSheet: `{spreadsheet_id}`\nRange: `{range_}`\nDati:\n```\n{rows_preview}\n```"
    return _queue("sheets_append", desc, {"spreadsheet_id": spreadsheet_id, "range_": range_, "values": values})


# ── Google Tasks ──────────────────────────────────────────────────────────────

def tasks_list(max_results: int = 20, include_completed: bool = False) -> dict:
    from integrations.gtasks import tasks_list as _tl
    return _tl(max_results, include_completed)


def tasks_create(title: str, tasklist_id: str = "@default",
                 due: str = "", notes: str = "") -> dict:
    due_str = f" — scadenza: {due}" if due else ""
    desc = f"✅ *Crea task*\nTitolo: _{title}_{due_str}\nLista: `{tasklist_id}`"
    return _queue("tasks_create", desc,
                  {"title": title, "tasklist_id": tasklist_id, "due": due, "notes": notes})


def tasks_complete(task_id: str, tasklist_id: str = "@default") -> dict:
    from integrations.gtasks import tasks_complete as _tc
    return _tc(task_id, tasklist_id)


# ── info (weather / stock / rss / pdf / youtube) ──────────────────────────────

def weather(city: str, units: str = "metric") -> dict:
    from integrations.info import weather as _weather
    return _weather(city, units)


def stock_price(ticker: str) -> dict:
    from integrations.info import stock_price as _stock
    return _stock(ticker)


def rss_feed(url: str, max_items: int = 10) -> dict:
    from integrations.info import rss_feed as _rss
    return _rss(url, max_items)


def pdf_read(source: str, max_pages: int = 20) -> dict:
    from integrations.info import pdf_read as _pdf
    return _pdf(source, max_pages)


def youtube_transcript(url: str, lang: str = "it") -> dict:
    from integrations.info import youtube_transcript as _yt
    return _yt(url, lang)


# ── web ───────────────────────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 8) -> dict:
    from integrations.web import search
    return search(query, max_results)


def web_fetch(url: str, max_chars: int = 8000) -> dict:
    from integrations.web import fetch
    return fetch(url, max_chars)


def web_scrape(url: str, selector: str = "", extract: str = "text") -> dict:
    from integrations.web import scrape
    return scrape(url, selector, extract)


# ── shell & python ─────────────────────────────────────────────────────────────

def shell_exec(command: str, timeout: int = 30) -> dict:
    """Run a shell command. Destructive patterns require Telegram approval."""
    if any(p in command for p in _SHELL_DANGEROUS):
        desc = f"🖥️ *Esegui comando shell*\n```\n{command}\n```"
        return _queue("shell_exec", desc, {"command": command, "timeout": timeout})
    try:
        res = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "command": command,
            "stdout": res.stdout[:4000],
            "stderr": res.stderr[:1000],
            "returncode": res.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout dopo {timeout}s", "command": command}


def python_exec(code: str, timeout: int = 30) -> dict:
    """Execute Python 3 code in a subprocess and return stdout/stderr."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        res = subprocess.run(
            ["python3", tmp], capture_output=True, text=True, timeout=timeout
        )
        return {
            "stdout": res.stdout[:4000],
            "stderr": res.stderr[:1000],
            "returncode": res.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout dopo {timeout}s"}
    finally:
        Path(tmp).unlink(missing_ok=True)


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


def memory_index() -> dict:
    from integrations.obsidian import read_index
    return read_index()


def memory_lint() -> dict:
    from integrations.obsidian import lint_vault
    return lint_vault()


def memory_ingest(title: str, content: str, folder: str = "Fonti") -> dict:
    from integrations.obsidian import ingest_source
    return ingest_source(title, content, folder)


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
            "name": "schedule_task",
            "description": "Programma un task futuro per Jarvis. Il cron trigger lo eseguirà automaticamente all'orario indicato e invierà il risultato su Telegram. Usa questo per reminder, report periodici, email ritardate, qualsiasi cosa da eseguire in futuro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Istruzione in linguaggio naturale da eseguire (es. 'Invia email di riassunto a mario@...')"},
                    "when": {"type": "string", "description": "Data/ora in formato ISO 8601, es. '2025-06-10T09:00:00+02:00'"},
                    "note": {"type": "string", "default": "", "description": "Descrizione breve opzionale"},
                },
                "required": ["task", "when"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_scheduled",
            "description": "Elenca i task schedulati in attesa di esecuzione.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_done": {"type": "boolean", "default": False, "description": "Includi anche i task già completati"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_scheduled",
            "description": "Annulla un task schedulato prima che venga eseguito.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID del task (da list_scheduled)"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_repos",
            "description": "Elenca i repository GitHub di un utente (o del tuo account se GITHUB_TOKEN è impostato).",
            "parameters": {
                "type": "object",
                "properties": {
                    "user":        {"type": "string", "default": "", "description": "Username GitHub. Vuoto = account autenticato."},
                    "max_results": {"type": "integer", "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_issues",
            "description": "Elenca le issue di un repository GitHub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo":        {"type": "string", "description": "Formato 'owner/repo-name'"},
                    "state":       {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                    "max_results": {"type": "integer", "default": 10},
                },
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_prs",
            "description": "Elenca le pull request di un repository GitHub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo":        {"type": "string", "description": "Formato 'owner/repo-name'"},
                    "state":       {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                    "max_results": {"type": "integer", "default": 10},
                },
                "required": ["repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_search",
            "description": "Cerca su GitHub (repo, issue, codice, utenti).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":       {"type": "string"},
                    "kind":        {"type": "string", "enum": ["repositories", "issues", "code", "users"], "default": "repositories"},
                    "max_results": {"type": "integer", "default": 8},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_stats",
            "description": "Statistiche sistema in tempo reale: CPU, RAM, disco, top processi, uptime. Non richiede alcuna configurazione.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "drive_list",
            "description": "Elenca i file in una cartella di Google Drive. Usa 'root' per la radice di My Drive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_id":   {"type": "string", "default": "root", "description": "ID cartella Drive o 'root'"},
                    "max_results": {"type": "integer", "default": 20},
                    "query":       {"type": "string", "default": "", "description": "Query Drive opzionale, es. \"name contains 'budget'\""},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "drive_read",
            "description": "Legge il contenuto testuale di un file Google Drive (Google Docs, Sheets, Slides, plain text). Ottieni l'ID dal file_id nella risposta di drive_list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "ID del file Google Drive"},
                },
                "required": ["file_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_read",
            "description": "Legge dati da un Google Sheet. Restituisce righe come lista di dizionari (header → valore).",
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string", "description": "ID dello spreadsheet (dalla URL Google Sheets)"},
                    "range_": {"type": "string", "default": "Sheet1", "description": "Range A1, es. 'Sheet1', 'Budget!A1:E20'"},
                },
                "required": ["spreadsheet_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_write",
            "description": "Scrive dati in un range di Google Sheets (richiede approvazione Telegram). Sovrascrive i dati esistenti.",
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_":  {"type": "string", "description": "Range A1, es. 'Sheet1!A1'"},
                    "values":  {"type": "array", "items": {"type": "array"}, "description": "Array 2D di valori, es. [[\"A\",\"B\"],[1,2]]"},
                },
                "required": ["spreadsheet_id", "range_", "values"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sheets_append",
            "description": "Aggiunge righe in fondo a un Google Sheet (richiede approvazione Telegram).",
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_":  {"type": "string", "default": "Sheet1"},
                    "values":  {"type": "array", "items": {"type": "array"}},
                },
                "required": ["spreadsheet_id", "range_", "values"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tasks_list",
            "description": "Elenca i task di Google Tasks (da tutte le liste). Mostra titolo, scadenza, note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results":        {"type": "integer", "default": 20},
                    "include_completed":  {"type": "boolean", "default": False},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tasks_create",
            "description": "Crea un task in Google Tasks (richiede approvazione Telegram).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":       {"type": "string", "description": "Titolo del task"},
                    "tasklist_id": {"type": "string", "default": "@default"},
                    "due":         {"type": "string", "default": "", "description": "Data scadenza ISO 8601, es. '2025-06-10T00:00:00.000Z'"},
                    "notes":       {"type": "string", "default": ""},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tasks_complete",
            "description": "Segna un task come completato in Google Tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id":     {"type": "string", "description": "ID del task (da tasks_list)"},
                    "tasklist_id": {"type": "string", "default": "@default"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "Meteo attuale e previsioni 3 giorni per qualsiasi città. Nessuna API key necessaria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city":  {"type": "string", "description": "Nome città, es. 'Milano', 'Roma', 'New York'"},
                    "units": {"type": "string", "enum": ["metric", "imperial"], "default": "metric"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_price",
            "description": "Prezzo in tempo reale di azioni, ETF o criptovalute. Usa ticker Yahoo Finance: AAPL, MSFT, BTC-USD, ETH-USD, ENI.MI, FTSEMIB.MI ecc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Ticker Yahoo Finance, es. 'AAPL', 'BTC-USD', 'ENI.MI'"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rss_feed",
            "description": "Legge un feed RSS o Atom e restituisce gli ultimi articoli. Funziona con blog, news, podcast, YouTube channel feed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url":       {"type": "string", "description": "URL del feed RSS/Atom"},
                    "max_items": {"type": "integer", "default": 10, "description": "Numero massimo di articoli"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pdf_read",
            "description": "Estrae il testo da un PDF (percorso locale o URL). Ideale per articoli, paper, documenti.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source":    {"type": "string", "description": "Percorso assoluto del file o URL HTTP/HTTPS"},
                    "max_pages": {"type": "integer", "default": 20, "description": "Pagine massime da estrarre"},
                },
                "required": ["source"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_transcript",
            "description": "Scarica la trascrizione di un video YouTube (sottotitoli automatici o manuali). Funziona con URL completo o video ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url":  {"type": "string", "description": "URL YouTube completo o video ID (11 caratteri)"},
                    "lang": {"type": "string", "default": "it", "description": "Codice lingua preferita (es. 'it', 'en'). Fallback automatico all'inglese."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Cerca sul web (DuckDuckGo o Brave). Usa per informazioni recenti, notizie, prezzi, meteo, qualsiasi cosa post-training.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":       {"type": "string", "description": "Query di ricerca in linguaggio naturale"},
                    "max_results": {"type": "integer", "default": 8},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Scarica il contenuto di un URL e lo restituisce come testo leggibile (HTML → markdown). Ideale per articoli, documentazione, pagine web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url":       {"type": "string", "description": "URL completo da scaricare"},
                    "max_chars": {"type": "integer", "default": 8000},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_scrape",
            "description": "Estrae dati strutturati da una pagina web. Più preciso di web_fetch per tabelle, liste, link o sezioni specifiche.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url":      {"type": "string"},
                    "selector": {"type": "string", "default": "", "description": "CSS selector, es. 'table', 'article p', '#content'. Vuoto = corpo pagina."},
                    "extract":  {
                        "type": "string",
                        "enum": ["text", "links", "table", "list", "html"],
                        "default": "text",
                        "description": "text=testo pulito, links=tutti i link, table=tabella come JSON, list=elementi lista, html=HTML grezzo",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shell_exec",
            "description": "Esegui un comando shell sul sistema locale. Comandi pericolosi (rm, sudo, kill...) richiedono approvazione Telegram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando bash da eseguire"},
                    "timeout": {"type": "integer", "default": 30, "description": "Timeout in secondi"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "python_exec",
            "description": "Esegui codice Python 3 in un subprocess e restituisci stdout/stderr. Usa per calcoli, analisi dati, grafici, manipolazione file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code":    {"type": "string", "description": "Codice Python da eseguire"},
                    "timeout": {"type": "integer", "default": 30},
                },
                "required": ["code"],
            },
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
    {
        "type": "function",
        "function": {
            "name": "memory_index",
            "description": "Legge l'indice della vault (index.md). Usalo PRIMA di memory_search per navigare la vault in modo efficiente.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_lint",
            "description": "Controlla la salute della vault: trova note orfane, link rotti, concetti senza pagina dedicata.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_ingest",
            "description": "Salva una fonte grezza (articolo, trascrizione, appunto) nella cartella Fonti/ come documento immutabile, poi suggerisce i passi per integrarlo nella wiki.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":   {"type": "string", "description": "Titolo della fonte"},
                    "content": {"type": "string", "description": "Contenuto completo della fonte"},
                    "folder":  {"type": "string", "default": "Fonti"},
                },
                "required": ["title", "content"],
            },
        },
    },
]

_DISPATCH: dict[str, callable] = {
    "schedule_task":    schedule_task,
    "list_scheduled":   list_scheduled,
    "cancel_scheduled": cancel_scheduled,
    "github_repos":   github_repos,
    "github_issues":  github_issues,
    "github_prs":     github_prs,
    "github_search":  github_search,
    "system_stats":   system_stats,
    "drive_list":     drive_list,
    "drive_read":     drive_read,
    "sheets_read":    sheets_read,
    "sheets_write":   sheets_write,
    "sheets_append":  sheets_append,
    "tasks_list":     tasks_list,
    "tasks_create":   tasks_create,
    "tasks_complete": tasks_complete,
    "weather":            weather,
    "stock_price":        stock_price,
    "rss_feed":           rss_feed,
    "pdf_read":           pdf_read,
    "youtube_transcript": youtube_transcript,
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
    "memory_index": memory_index,
    "memory_lint": memory_lint,
    "memory_ingest": memory_ingest,
    "web_search":   web_search,
    "web_fetch":    web_fetch,
    "web_scrape":   web_scrape,
    "shell_exec":   shell_exec,
    "python_exec":  python_exec,
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
