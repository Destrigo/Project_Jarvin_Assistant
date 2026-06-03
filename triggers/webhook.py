"""HTTP webhook trigger — uv run jarvis-web"""
import os
import json as _json
import threading
import queue as _queue
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import uvicorn

from agent.loop import run, stream_run
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


@app.post("/task/stream")
async def handle_task_stream(req: TaskRequest):
    if _SECRET and req.secret != _SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

    import asyncio

    async def generate():
        loop = asyncio.get_running_loop()
        q: _queue.Queue = _queue.Queue()

        def producer():
            try:
                for event in stream_run(req.task):
                    q.put(event)
            except Exception as exc:
                q.put({"event": "error", "data": {"message": str(exc)}})
            finally:
                q.put(None)

        threading.Thread(target=producer, daemon=True).start()

        reply = ""
        while True:
            event = await loop.run_in_executor(None, q.get)
            if event is None:
                break
            if event["event"] == "done":
                reply = event["data"].get("reply", "")
            sse = f"event: {event['event']}\ndata: {_json.dumps(event['data'], ensure_ascii=False)}\n\n"
            yield sse.encode()

        store.append_message("user", req.task)
        store.append_message("assistant", reply)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/email/{email_id}")
def get_email(email_id: str):
    from integrations.gmail import read_email
    return read_email(email_id)


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


@app.get("/memory/note")
def get_note(title: str):
    from pathlib import Path
    vault = Path(os.getenv("OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis"))).expanduser()
    matches = list(vault.rglob(f"{title}.md"))
    if not matches:
        raise HTTPException(status_code=404, detail="Note not found")
    content = matches[0].read_text(encoding="utf-8", errors="ignore")
    rel = str(matches[0].relative_to(vault))
    folder = rel.split("/")[0] if "/" in rel else ""
    return {"title": title, "content": content, "path": rel, "folder": folder}


@app.get("/memory/graph")
def memory_graph():
    """Return nodes and edges for the Obsidian vault graph visualization."""
    import re
    from pathlib import Path
    vault = Path(os.getenv("OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis"))).expanduser()
    vault.mkdir(parents=True, exist_ok=True)
    nodes, edges = [], []
    id_map = {}
    files = list(vault.rglob("*.md"))
    for i, f in enumerate(files):
        rel = str(f.relative_to(vault))
        folder = rel.split("/")[0] if "/" in rel else ""
        id_map[f.stem] = i
        nodes.append({"id": i, "name": f.stem, "path": rel,
                      "folder": folder, "size": f.stat().st_size})
    link_re = re.compile(r'\[\[([^\]|#]+)')
    for f in files:
        src = id_map.get(f.stem)
        if src is None: continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in link_re.finditer(text):
            target_name = m.group(1).strip()
            dst = id_map.get(target_name)
            if dst is not None and dst != src:
                edges.append({"source": src, "target": dst})
    return {"nodes": nodes, "links": edges}


@app.get("/stats")
def get_stats():
    from pathlib import Path
    vault = Path(os.getenv("OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis"))).expanduser()
    notes = list(vault.rglob("*.md"))
    memoria = [n for n in notes if "Memoria" in str(n)]
    conv = [n for n in notes if "Conversazioni" in str(n)]
    history = store.get_history(n=200)
    user_msgs = [m for m in history if m["role"] == "user"]
    pending = store.pending_actions()
    resolved = [a for a in store._load()["pending"].values()
                if a["status"] != "pending"]
    return {
        "vault": {
            "total_notes": len(notes),
            "memory_notes": len(memoria),
            "conversation_notes": len(conv),
        },
        "conversations": {
            "total_messages": len(history),
            "user_messages": len(user_msgs),
        },
        "approvals": {
            "pending": len(pending),
            "resolved": len(resolved),
        },
    }


@app.post("/tts")
async def tts_endpoint(request: Request):
    """Generate speech from text using Kokoro TTS. Returns audio/wav."""
    import asyncio
    body = await request.json()
    text = body.get("text", "").strip()
    voice = body.get("voice", None)
    speed = body.get("speed", None)

    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    loop = asyncio.get_running_loop()
    try:
        from integrations.tts import synthesize
        wav_bytes = await loop.run_in_executor(None, lambda: synthesize(text, voice, speed))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/tts/voices")
def tts_voices():
    """Return available TTS voices."""
    from integrations.tts import VOICES, _DEFAULT_VOICE
    return {"voices": VOICES, "default": _DEFAULT_VOICE}


@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    uvicorn.run("triggers.webhook:app", host="0.0.0.0", port=8080, reload=False)
