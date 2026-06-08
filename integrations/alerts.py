"""Persistent alert monitor.

Alerts are stored in memory/alerts.json. Each alert has a condition_code — a
Python expression string that is evaluated periodically by the cron trigger.
If the expression evaluates to True (and cooldown has elapsed), Jarvis sends
a Telegram notification.

condition_code examples:
  float(stock_price('AAPL').get('price', 99999)) < 150
  len(list_emails(max_results=1, query='from:boss@co.com is:unread').get('emails', [])) > 0
  system_stats().get('cpu_percent', 0) > 90
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

_STORE = Path(os.environ.get("JARVIS_HOME", Path(__file__).parent.parent)) / "memory" / "alerts.json"


def _load() -> list[dict]:
    if _STORE.exists():
        try:
            return json.loads(_STORE.read_text())
        except Exception:
            pass
    return []


def _save(alerts: list[dict]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(alerts, indent=2, ensure_ascii=False))


def create_alert(name: str, condition_code: str, message: str,
                 repeat: bool = True, cooldown_hours: float = 1.0) -> dict:
    """Create a new alert.

    name:           human-readable name (e.g. "AAPL sotto 150")
    condition_code: Python expression → bool. Has access to all Jarvis tool functions.
    message:        text sent to Telegram when the condition fires.
    repeat:         if False, the alert fires once then disables itself.
    cooldown_hours: minimum hours between two triggers (avoids spam).
    """
    alert_id = uuid.uuid4().hex[:8]
    entry = {
        "id": alert_id,
        "name": name,
        "condition_code": condition_code,
        "message": message,
        "status": "active",
        "repeat": repeat,
        "cooldown_hours": cooldown_hours,
        "last_triggered": None,
        "trigger_count": 0,
        "created": datetime.now(timezone.utc).isoformat(),
    }
    alerts = _load()
    alerts.append(entry)
    _save(alerts)
    return {"created": True, "id": alert_id, "name": name,
            "message": f"Alert '{name}' attivo (cooldown {cooldown_hours}h, repeat={repeat})"}


def list_alerts(include_paused: bool = True) -> dict:
    alerts = _load()
    if not include_paused:
        alerts = [a for a in alerts if a["status"] == "active"]
    return {"alerts": alerts, "count": len(alerts)}


def delete_alert(alert_id: str) -> dict:
    alerts = _load()
    before = len(alerts)
    removed = next((a for a in alerts if a["id"] == alert_id), None)
    alerts = [a for a in alerts if a["id"] != alert_id]
    if len(alerts) == before:
        return {"error": f"Alert '{alert_id}' non trovato."}
    _save(alerts)
    return {"deleted": True, "id": alert_id, "name": removed.get("name", "")}


def pause_alert(alert_id: str, paused: bool = True) -> dict:
    alerts = _load()
    for a in alerts:
        if a["id"] == alert_id:
            a["status"] = "paused" if paused else "active"
            _save(alerts)
            return {"id": alert_id, "name": a["name"], "status": a["status"]}
    return {"error": f"Alert '{alert_id}' non trovato."}


def check_alerts() -> list[dict]:
    """Evaluate all active alerts. Returns list of dicts for each triggered alert.

    Called by the cron trigger every CHECK_ALERTS_MIN minutes.
    Condition expressions have access to all Jarvis tool functions.
    """
    alerts = _load()
    if not alerts:
        return []

    now = datetime.now(timezone.utc)
    triggered = []
    changed = False

    # Build eval namespace: all dispatchable tool functions
    from agent.tools import _DISPATCH
    _safe_builtins = {
        "__builtins__": {
            "float": float, "int": int, "str": str, "bool": bool,
            "len": len, "abs": abs, "min": min, "max": max,
            "list": list, "dict": dict, "None": None, "True": True, "False": False,
        }
    }
    ns = {**_safe_builtins, **_DISPATCH}

    for alert in alerts:
        if alert["status"] != "active":
            continue

        # Enforce cooldown
        if alert.get("last_triggered"):
            try:
                last = datetime.fromisoformat(alert["last_triggered"])
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                hours_elapsed = (now - last).total_seconds() / 3600
                if hours_elapsed < float(alert.get("cooldown_hours", 1.0)):
                    continue
            except Exception:
                pass

        # Evaluate condition
        try:
            result = bool(eval(alert["condition_code"], ns))  # noqa: S307
        except Exception:
            continue

        if result:
            triggered.append({
                "id": alert["id"],
                "name": alert["name"],
                "message": alert["message"],
            })
            alert["last_triggered"] = now.isoformat()
            alert["trigger_count"] = alert.get("trigger_count", 0) + 1
            if not alert.get("repeat", True):
                alert["status"] = "triggered_once"
            changed = True

    if changed:
        _save(alerts)

    return triggered
