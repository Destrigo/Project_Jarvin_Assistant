"""Simple JSON-backed state store for pending approvals and conversation history."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

_PATH = Path(__file__).parent / "store.json"


def _load() -> dict:
    if not _PATH.exists():
        return {"pending": {}, "history": []}
    return json.loads(_PATH.read_text())


def _save(data: dict) -> None:
    _PATH.write_text(json.dumps(data, indent=2, default=str))


# ── pending approvals ─────────────────────────────────────────────────────────

def queue_action(action_type: str, description: str, payload: dict) -> str:
    """Save a pending action and return its ID."""
    data = _load()
    action_id = str(uuid.uuid4())[:8]
    data["pending"][action_id] = {
        "id": action_id,
        "type": action_type,
        "description": description,
        "payload": payload,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    _save(data)
    return action_id


def get_action(action_id: str) -> dict | None:
    return _load()["pending"].get(action_id)


def resolve_action(action_id: str, status: Literal["approved", "skipped"]) -> dict | None:
    data = _load()
    action = data["pending"].get(action_id)
    if action:
        action["status"] = status
        action["resolved_at"] = datetime.utcnow().isoformat()
        _save(data)
    return action


def pending_actions() -> list[dict]:
    return [a for a in _load()["pending"].values() if a["status"] == "pending"]


# ── conversation history ───────────────────────────────────────────────────────

def append_message(role: str, content: str) -> None:
    data = _load()
    data["history"].append({"role": role, "content": content,
                            "ts": datetime.utcnow().isoformat()})
    # keep last 50 messages to avoid context bloat
    data["history"] = data["history"][-50:]
    _save(data)


def get_history(n: int = 20) -> list[dict]:
    return [{"role": m["role"], "content": m["content"]}
            for m in _load()["history"][-n:]]


def clear_history() -> None:
    data = _load()
    data["history"] = []
    _save(data)
