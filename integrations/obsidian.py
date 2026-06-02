"""Obsidian vault integration — read/write markdown notes as agent memory."""
import os
import re
from datetime import datetime
from pathlib import Path

_VAULT = Path(os.getenv("OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis"))).expanduser()


def _vault_path() -> Path:
    _VAULT.mkdir(parents=True, exist_ok=True)
    return _VAULT


def write_note(title: str, content: str, folder: str = "") -> dict:
    base = _vault_path() / folder if folder else _vault_path()
    base.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/*?:"<>|]', "-", title)
    path = base / f"{safe}.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    full = f"# {title}\n*{now}*\n\n{content}\n"
    path.write_text(full, encoding="utf-8")
    return {"status": "written", "path": str(path)}


def read_note(title: str, folder: str = "") -> dict:
    base = _vault_path() / folder if folder else _vault_path()
    safe = re.sub(r'[\\/*?:"<>|]', "-", title)
    path = base / f"{safe}.md"
    if not path.exists():
        return {"error": f"Nota non trovata: {title}"}
    return {"title": title, "content": path.read_text(encoding="utf-8")}


def list_notes(folder: str = "") -> dict:
    base = _vault_path() / folder if folder else _vault_path()
    if not base.exists():
        return {"notes": []}
    notes = [p.stem for p in sorted(base.rglob("*.md"))]
    return {"vault": str(_vault_path()), "notes": notes}


def search_notes(query: str) -> dict:
    """Full-text search across all notes in the vault."""
    results = []
    q = query.lower()
    for path in _vault_path().rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if q in text.lower():
            # return first matching line as snippet
            snippet = next(
                (line.strip() for line in text.splitlines() if q in line.lower()), ""
            )
            results.append({
                "title": path.stem,
                "path": str(path.relative_to(_vault_path())),
                "snippet": snippet[:200],
            })
    return {"query": query, "results": results}


def append_to_note(title: str, content: str, folder: str = "") -> dict:
    """Append content to an existing note (or create it)."""
    base = _vault_path() / folder if folder else _vault_path()
    base.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/*?:"<>|]', "-", title)
    path = base / f"{safe}.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if path.exists():
        path.open("a", encoding="utf-8").write(f"\n---\n*{now}*\n{content}\n")
    else:
        path.write_text(f"# {title}\n*{now}*\n\n{content}\n", encoding="utf-8")
    return {"status": "appended", "path": str(path)}


def save_conversation_summary(summary: str) -> dict:
    """Save a daily conversation summary to the vault."""
    today = datetime.now().strftime("%Y-%m-%d")
    return append_to_note(today, summary, folder="Conversazioni")
