"""Gmail integration via Google API (OAuth2)."""
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from integrations.google_auth import get_credentials


def _service():
    return build("gmail", "v1", credentials=get_credentials())


def list_emails(max_results: int = 10, query: str = "is:unread") -> list[dict]:
    svc = _service()
    resp = svc.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = resp.get("messages", [])
    result = []
    for m in messages:
        msg = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        result.append({
            "id": m["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return result


def read_email(email_id: str) -> dict:
    svc = _service()
    msg = svc.users().messages().get(
        userId="me", id=email_id, format="full"
    ).execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    body = ""
    parts = msg["payload"].get("parts", [])
    if parts:
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part["body"].get("data", "")
                body = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
                break
    else:
        data = msg["payload"]["body"].get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")

    return {
        "id": email_id,
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "body": body[:4000],  # cap at 4k chars
    }


def send_email(to: str, subject: str, body: str) -> dict:
    svc = _service()
    mime = MIMEText(body)
    mime["to"] = to
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"status": "sent", "to": to, "subject": subject}


def mark_read(email_id: str) -> None:
    svc = _service()
    svc.users().messages().modify(
        userId="me", id=email_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()
