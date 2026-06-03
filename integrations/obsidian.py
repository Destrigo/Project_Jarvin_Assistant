"""Obsidian vault integration — read/write markdown notes as agent memory."""
import os
import re
from datetime import datetime
from pathlib import Path

_VAULT = Path(os.getenv("OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis"))).expanduser()


def _vault_path() -> Path:
    _VAULT.mkdir(parents=True, exist_ok=True)
    return _VAULT


def _safe(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "-", title)


# ── index & log ────────────────────────────────────────────────────────────────

def _update_index() -> None:
    """Rebuild index.md — the AI reads this first to navigate the vault."""
    vault = _vault_path()
    notes = [p for p in sorted(vault.rglob("*.md")) if p.name not in ("index.md", "log.md")]
    by_folder: dict[str, list[Path]] = {}
    for note in notes:
        rel = str(note.relative_to(vault))
        folder = rel.split("/")[0] if "/" in rel else ""
        by_folder.setdefault(folder, []).append(note)

    lines = ["# Index della vault\n*Aggiornato automaticamente — leggi questo prima di cercare note*\n"]
    for folder, paths in sorted(by_folder.items()):
        lines.append(f"\n## {folder or 'Root'}\n")
        for p in sorted(paths):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                summary = next(
                    (l.strip() for l in text.splitlines()[2:] if l.strip() and not l.startswith("#")),
                    "",
                )[:120]
            except Exception:
                summary = ""
            lines.append(f"- [[{p.stem}]] — {summary}\n")

    (vault / "index.md").write_text("".join(lines), encoding="utf-8")


def _log(operation: str, detail: str) -> None:
    """Append one entry to log.md."""
    vault = _vault_path()
    log_path = vault / "log.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## [{now}] {operation}\n{detail}\n"
    if log_path.exists():
        with log_path.open("a", encoding="utf-8") as f:
            f.write(entry)
    else:
        log_path.write_text(f"# Log operazioni\n{entry}", encoding="utf-8")


# ── CRUD ──────────────────────────────────────────────────────────────────────

def write_note(title: str, content: str, folder: str = "") -> dict:
    base = _vault_path() / folder if folder else _vault_path()
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{_safe(title)}.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    path.write_text(f"# {title}\n*{now}*\n\n{content}\n", encoding="utf-8")
    _update_index()
    _log("write", f"[[{title}]] in {folder or 'root'}")
    return {"status": "written", "path": str(path)}


def read_note(title: str, folder: str = "") -> dict:
    base = _vault_path() / folder if folder else _vault_path()
    path = base / f"{_safe(title)}.md"
    if not path.exists():
        # fallback: search anywhere in vault
        matches = list(_vault_path().rglob(f"{_safe(title)}.md"))
        if not matches:
            return {"error": f"Nota non trovata: {title}"}
        path = matches[0]
    return {"title": title, "content": path.read_text(encoding="utf-8")}


def list_notes(folder: str = "") -> dict:
    base = _vault_path() / folder if folder else _vault_path()
    if not base.exists():
        return {"notes": []}
    notes = [p.stem for p in sorted(base.rglob("*.md")) if p.name not in ("index.md", "log.md")]
    return {"vault": str(_vault_path()), "notes": notes}


def search_notes(query: str) -> dict:
    results = []
    q = query.lower()
    for path in _vault_path().rglob("*.md"):
        if path.name in ("index.md", "log.md"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if q in text.lower():
            snippet = next((l.strip() for l in text.splitlines() if q in l.lower()), "")
            results.append({
                "title": path.stem,
                "path": str(path.relative_to(_vault_path())),
                "snippet": snippet[:200],
            })
    return {"query": query, "results": results}


def append_to_note(title: str, content: str, folder: str = "") -> dict:
    base = _vault_path() / folder if folder else _vault_path()
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{_safe(title)}.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if path.exists():
        with path.open("a", encoding="utf-8") as f:
            f.write(f"\n---\n*{now}*\n{content}\n")
    else:
        path.write_text(f"# {title}\n*{now}*\n\n{content}\n", encoding="utf-8")
    _update_index()
    _log("append", f"[[{title}]]")
    return {"status": "appended", "path": str(path)}


def save_conversation_summary(summary: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    return append_to_note(today, summary, folder="Conversazioni")


# ── index / lint / ingest ──────────────────────────────────────────────────────

def read_index() -> dict:
    """Return the index.md content (or rebuild if missing)."""
    vault = _vault_path()
    index_path = vault / "index.md"
    if not index_path.exists():
        _update_index()
    return {"content": index_path.read_text(encoding="utf-8")}


def lint_vault() -> dict:
    """Health-check: find orphan notes, broken links, concepts without a page."""
    vault = _vault_path()
    link_re = re.compile(r'\[\[([^\]|#]+)')

    all_stems = {
        p.stem for p in vault.rglob("*.md")
        if p.name not in ("index.md", "log.md")
    }

    inbound: dict[str, int] = {s: 0 for s in all_stems}
    broken_links: list[dict] = []

    for path in vault.rglob("*.md"):
        if path.name in ("index.md", "log.md"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in link_re.finditer(text):
            target = m.group(1).strip()
            if target in inbound:
                inbound[target] += 1
            else:
                broken_links.append({"from": path.stem, "target": target})

    orphans = [s for s, count in inbound.items() if count == 0]

    report = {
        "total_notes": len(all_stems),
        "orphan_notes": orphans,
        "orphan_count": len(orphans),
        "broken_links": broken_links[:20],
        "broken_link_count": len(broken_links),
        "suggestions": [],
    }

    if orphans:
        report["suggestions"].append(
            f"Collega o rimuovi le {len(orphans)} note orfane: {', '.join(orphans[:5])}"
        )
    if broken_links:
        report["suggestions"].append(
            f"Crea pagine per i {len(broken_links)} link mancanti: "
            + ", ".join({b['target'] for b in broken_links[:5]})
        )

    _log("lint", f"Trovati {len(orphans)} orfani, {len(broken_links)} link rotti")
    return report


def ingest_source(title: str, content: str, folder: str = "Fonti") -> dict:
    """Save a raw source (immutable) and return a structured summary prompt."""
    vault = _vault_path()
    base = vault / folder
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{_safe(title)}.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if path.exists():
        return {"status": "already_exists", "path": str(path),
                "message": f"La fonte '{title}' esiste già in {folder}/"}

    path.write_text(
        f"# {title}\n*Acquisita: {now}*\n\n{content}\n",
        encoding="utf-8",
    )
    _update_index()
    _log("ingest", f"Nuova fonte: [[{title}]] in {folder}/")

    return {
        "status": "ingested",
        "path": str(path),
        "next_step": (
            f"Ora estrai i concetti chiave da '{title}', crea/aggiorna le note rilevanti "
            f"in Memoria/ usando memory_write, e aggiorna le note esistenti che si collegano "
            f"a questi concetti usando memory_append."
        ),
    }
