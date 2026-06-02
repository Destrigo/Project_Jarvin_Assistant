"""HTTP webhook trigger — uv run jarvis-web"""
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agent.loop import run
import memory.store as store

app = FastAPI(title="Jarvis", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_SECRET = os.getenv("WEBHOOK_SECRET", "")


class TaskRequest(BaseModel):
    task: str
    secret: str = ""


@app.post("/task")
def handle_task(req: TaskRequest):
    if _SECRET and req.secret != _SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")
    reply = run(req.task)
    store.append_message("user", req.task)
    store.append_message("assistant", reply)
    return {"reply": reply, "pending_approvals": len(store.pending_actions())}


@app.get("/history")
def get_history():
    return {"messages": store.get_history(n=50)}


@app.get("/emails")
def get_emails(max_results: int = 10, query: str = "is:unread"):
    from integrations.gmail import list_emails
    return {"emails": list_emails(max_results=max_results, query=query)}


@app.get("/events")
def get_events(days_ahead: int = 7):
    from integrations.calendar import list_events
    return {"events": list_events(days_ahead=days_ahead)}


@app.get("/pending")
def get_pending():
    return {"pending": store.pending_actions()}


@app.post("/resolve/{action_id}")
def resolve(action_id: str, status: str = "approved"):
    if status not in ("approved", "skipped"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'skipped'")
    action = store.resolve_action(action_id, status)  # type: ignore[arg-type]
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if status == "approved":
        from integrations.telegram import _execute_approved
        result = _execute_approved(action)
        return {"status": "approved", "result": result}
    return {"status": "skipped"}


@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    uvicorn.run("triggers.webhook:app", host="0.0.0.0", port=8080, reload=False)
