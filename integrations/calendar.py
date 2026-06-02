"""Google Calendar integration."""
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from integrations.google_auth import get_credentials


def _service():
    return build("calendar", "v3", credentials=get_credentials())
    return build("calendar", "v3", credentials=creds)


def list_events(days_ahead: int = 7) -> list[dict]:
    svc = _service()
    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"
    resp = svc.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()
    events = []
    for e in resp.get("items", []):
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        events.append({
            "id": e["id"],
            "title": e.get("summary", "(no title)"),
            "start": start,
            "end": e["end"].get("dateTime", e["end"].get("date", "")),
            "description": e.get("description", ""),
            "attendees": [a["email"] for a in e.get("attendees", [])],
        })
    return events


def create_event(
    title: str,
    start: str,
    end: str,
    description: str = "",
    attendees: list[str] | None = None,
) -> dict:
    """
    start/end: ISO 8601 strings, e.g. "2025-06-10T14:00:00+02:00"
    """
    svc = _service()
    body: dict = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    if attendees:
        body["attendees"] = [{"email": e} for e in attendees]
    event = svc.events().insert(calendarId="primary", body=body).execute()
    return {"id": event["id"], "title": title, "start": start, "end": end,
            "link": event.get("htmlLink", "")}


def delete_event(event_id: str) -> dict:
    svc = _service()
    svc.events().delete(calendarId="primary", eventId=event_id).execute()
    return {"status": "deleted", "id": event_id}
