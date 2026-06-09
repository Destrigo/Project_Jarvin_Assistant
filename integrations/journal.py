"""Diario personale — salva appunti da Telegram e genera riassunto settimanale."""
import os
from datetime import date, timedelta, datetime
from pathlib import Path


def _vault() -> Path:
    return Path(os.environ.get("OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Jarvis")))


def _day_file(d: date | None = None) -> Path:
    folder = _vault() / "Diario"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{(d or date.today()).isoformat()}.md"


def save_entry(text: str, source: str = "telegram") -> Path:
    """Aggiunge un'entrata timestampata al diario di oggi."""
    now = datetime.now().strftime("%H:%M")
    f = _day_file()
    if not f.exists():
        f.write_text(f"# Diario {date.today().isoformat()}\n\n", encoding="utf-8")
    with f.open("a", encoding="utf-8") as fp:
        fp.write(f"**{now}** _{source}_\n{text.strip()}\n\n")
    return f


def get_week_entries() -> dict[str, str]:
    """Restituisce le entrate della settimana corrente (lunedì → oggi)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    entries = {}
    for i in range(7):
        d = monday + timedelta(days=i)
        if d > today:
            break
        f = _day_file(d)
        if f.exists():
            entries[d.isoformat()] = f.read_text(encoding="utf-8")
    return entries


def _transcribe(filepath: str) -> str | None:
    """Trascrive un file audio con faster-whisper (tiny). Restituisce None se non disponibile."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(filepath, beam_size=1)
        return " ".join(s.text.strip() for s in segments).strip() or None
    except ImportError:
        return None
    except Exception:
        return None
