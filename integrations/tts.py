"""Kokoro TTS integration — local neural text-to-speech."""
import io
import os
import re
import threading
from pathlib import Path

import soundfile as sf

_MODELS_DIR = Path(__file__).parent.parent / "models"
_MODEL_PATH = str(_MODELS_DIR / "kokoro-v1.0.int8.onnx")
_VOICES_PATH = str(_MODELS_DIR / "voices-v1.0.bin")

_DEFAULT_VOICE = os.environ.get("TTS_VOICE", "if_sara")
_DEFAULT_SPEED = float(os.environ.get("TTS_SPEED", "1.0"))

_kokoro = None
_lock = threading.Lock()

VOICES = {
    # Italian
    "if_sara":    "Sara (IT, F)",
    "im_nicola":  "Nicola (IT, M)",
    # English
    "af_heart":   "Heart (EN-US, F)",
    "af_bella":   "Bella (EN-US, F)",
    "am_adam":    "Adam (EN-US, M)",
    "bf_emma":    "Emma (EN-GB, F)",
    "bm_george":  "George (EN-GB, M)",
}

# map voice prefix to lang code
_VOICE_LANG = {
    "if": "it", "im": "it",
    "af": "en-us", "am": "en-us",
    "bf": "en-gb", "bm": "en-gb",
    "ff": "fr-fr", "zf": "zh", "zm": "zh",
    "jf": "ja", "jm": "ja",
}


def _get_kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(_MODEL_PATH, _VOICES_PATH)
    return _kokoro


def _clean_text(text: str) -> str:
    """Strip markdown and normalize whitespace for TTS."""
    text = re.sub(r"```[\s\S]*?```", "", text)       # code blocks
    text = re.sub(r"`[^`]+`", "", text)               # inline code
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links → anchor text
    text = re.sub(r"[#*_~>|]", "", text)              # markdown symbols
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\n", " ").strip()
    return text


def _split_chunks(text: str, max_chars: int = 400) -> list[str]:
    """Split text into sentence-boundary chunks to stay under Kokoro phoneme limit."""
    sentences = re.split(r"(?<=[.!?;:])\s+", text)
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) + 1 <= max_chars:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s[:max_chars]  # hard truncate if a single sentence is too long
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def synthesize(text: str, voice: str | None = None, speed: float | None = None) -> bytes:
    """Convert text to WAV audio bytes using Kokoro.

    Returns raw WAV bytes ready to send as audio/wav response.
    """
    voice = voice or _DEFAULT_VOICE
    speed = speed if speed is not None else _DEFAULT_SPEED
    lang = _VOICE_LANG.get(voice[:2], "en-us")

    clean = _clean_text(text)
    if not clean:
        return b""

    chunks = _split_chunks(clean)

    import numpy as np

    with _lock:
        k = _get_kokoro()
        all_samples = []
        sample_rate = 24000
        for chunk in chunks:
            samples, sr = k.create(chunk, voice=voice, speed=speed, lang=lang)
            sample_rate = sr
            all_samples.append(samples)
            # small silence between sentences (0.15s)
            all_samples.append(np.zeros(int(sr * 0.15), dtype=np.float32))

        audio = np.concatenate(all_samples) if all_samples else np.array([], dtype=np.float32)

    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()
