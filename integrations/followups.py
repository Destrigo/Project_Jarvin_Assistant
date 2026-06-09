"""Follow-up tracker: notifica quando una mail inviata non ha risposta."""
import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_home = Path(os.environ.get("JARVIS_HOME", Path(__file__).parent.parent))
_PATH = _home / "memory" / "followups.json"


def _load() -> list[dict]:
    if _PATH.exists():
        return json.loads(_PATH.read_text())
    return []


def _save(data: list[dict]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def add(to: str, subject: str, days: int = 3) -> dict:
    """Inizia a tracciare una mail inviata per follow-up dopo N giorni."""
    data = _load()
    entry = {
        "id": uuid.uuid4().hex[:8],
        "to": to,
        "subject": subject,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "followup_days": days,
        "done": False,
    }
    data.append(entry)
    _save(data)
    return entry


def dismiss(entry_id: str) -> bool:
    data = _load()
    for e in data:
        if e["id"] == entry_id:
            e["done"] = True
            _save(data)
            return True
    return False


def list_pending() -> list[dict]:
    return [e for e in _load() if not e.get("done")]


def check() -> list[dict]:
    """Controlla le mail overdue e marca quelle che hanno ricevuto risposta."""
    data = _load()
    overdue = []
    updated = False
    now = datetime.now(timezone.utc)

    try:
        from integrations.google_auth import get_credentials
        from googleapiclient.discovery import build
        creds = get_credentials()
        svc = build("gmail", "v1", credentials=creds)
    except Exception:
        return []

    for entry in data:
        if entry.get("done"):
            continue
        sent_at = datetime.fromisoformat(entry["sent_at"])
        days_elapsed = (now - sent_at).total_seconds() / 86400
        if days_elapsed < entry["followup_days"]:
            continue

        # Cerca una risposta: subject "Re: ..." ricevuta dopo l'invio
        sent_date = sent_at.strftime("%Y/%m/%d")
        q = f'in:inbox subject:"Re: {entry["subject"]}" after:{sent_date}'
        try:
            result = svc.users().messages().list(userId="me", q=q, maxResults=1).execute()
            if result.get("messages"):
                entry["done"] = True
                updated = True
                continue
        except Exception:
            pass

        overdue.append(entry)

    if updated:
        _save(data)
    return overdue
