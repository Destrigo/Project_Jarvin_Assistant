"""Persistent task scheduler — Jarvis can schedule future tasks for itself.

Tasks are stored in memory/scheduled_tasks.json and executed by the cron trigger.
Each task has: id, when (ISO 8601), task (the instruction to run), status.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

_STORE = Path(os.environ.get("JARVIS_HOME", Path(__file__).parent.parent)) / "memory" / "scheduled_tasks.json"


def _load() -> list[dict]:
    if _STORE.exists():
        try:
            return json.loads(_STORE.read_text())
        except Exception:
            pass
    return []


def _save(tasks: list[dict]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))


def schedule_task(task: str, when: str, note: str = "") -> dict:
    """Schedule a future task for Jarvis to execute autonomously.

    task: natural language instruction (e.g. "Invia email di riassunto settimanale a...")
    when: ISO 8601 datetime string (e.g. "2025-06-10T09:00:00+02:00")
    note: optional human-readable description
    """
    try:
        dt = datetime.fromisoformat(when)
        if dt.tzinfo is None:
            # assume local time → attach local timezone
            dt = dt.astimezone()
    except ValueError:
        return {"error": f"Formato datetime non valido: '{when}'. Usa ISO 8601, es. 2025-06-10T09:00:00+02:00"}

    task_id = uuid.uuid4().hex[:8]
    entry = {
        "id":     task_id,
        "task":   task,
        "note":   note or task[:80],
        "when":   dt.isoformat(),
        "status": "pending",
        "created": datetime.now(timezone.utc).isoformat(),
    }
    tasks = _load()
    tasks.append(entry)
    _save(tasks)

    return {
        "scheduled": True,
        "id": task_id,
        "task": task,
        "when": dt.strftime("%d/%m/%Y alle %H:%M"),
    }


def list_scheduled(include_done: bool = False) -> dict:
    """List all scheduled tasks."""
    tasks = _load()
    if not include_done:
        tasks = [t for t in tasks if t["status"] == "pending"]
    tasks.sort(key=lambda t: t["when"])
    return {"tasks": tasks, "count": len(tasks)}


def cancel_scheduled(task_id: str) -> dict:
    """Cancel a scheduled task by ID."""
    tasks = _load()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "cancelled"
            _save(tasks)
            return {"cancelled": True, "id": task_id, "task": t["task"]}
    return {"error": f"Task '{task_id}' non trovato."}


def pop_due_tasks() -> list[dict]:
    """Return and mark as 'running' all tasks due now or in the past.

    Called by the cron trigger to pick up pending work.
    """
    now = datetime.now(timezone.utc)
    tasks = _load()
    due = []
    for t in tasks:
        if t["status"] != "pending":
            continue
        try:
            when = datetime.fromisoformat(t["when"])
            if when.tzinfo is None:
                when = when.astimezone(timezone.utc)
            if when <= now:
                t["status"] = "running"
                due.append(t)
        except Exception:
            pass
    if due:
        _save(tasks)
    return due


def mark_done(task_id: str, result: str = "") -> None:
    tasks = _load()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            t["result"] = result[:500]
            t["done_at"] = datetime.now(timezone.utc).isoformat()
            break
    _save(tasks)
