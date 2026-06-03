"""Information tools: weather, stock/crypto, RSS, PDF, YouTube transcripts."""
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
_TIMEOUT = 15


# ── weather ───────────────────────────────────────────────────────────────────

def weather(city: str, units: str = "metric") -> dict:
    """Current weather + 3-day forecast via wttr.in (no API key required).

    units: "metric" (°C) or "imperial" (°F)
    """
    unit_param = "" if units == "metric" else "&u"
    url = f"https://wttr.in/{requests.utils.quote(city)}?format=j1{unit_param}"
    resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    unit_label = "°C" if units == "metric" else "°F"
    speed_label = "km/h" if units == "metric" else "mph"

    current = data["current_condition"][0]
    current_out = {
        "temp": f"{current['temp_C']}{unit_label}" if units == "metric" else f"{current['temp_F']}{unit_label}",
        "feels_like": f"{current['FeelsLikeC']}{unit_label}" if units == "metric" else f"{current['FeelsLikeF']}{unit_label}",
        "description": current["weatherDesc"][0]["value"],
        "humidity": f"{current['humidity']}%",
        "wind": f"{current['windspeedKmph']} {speed_label}" if units == "metric" else f"{current['windspeedMiles']} {speed_label}",
        "visibility": f"{current['visibility']} km",
        "uv_index": current.get("uvIndex", "n/a"),
    }

    forecast = []
    for day in data.get("weather", [])[:3]:
        forecast.append({
            "date": day["date"],
            "max": f"{day['maxtempC']}{unit_label}" if units == "metric" else f"{day['maxtempF']}{unit_label}",
            "min": f"{day['mintempC']}{unit_label}" if units == "metric" else f"{day['mintempF']}{unit_label}",
            "description": day["hourly"][4]["weatherDesc"][0]["value"],
            "rain_mm": day.get("totalSnow_cm", "0"),
            "sunrise": day["astronomy"][0].get("sunrise", ""),
            "sunset": day["astronomy"][0].get("sunset", ""),
        })

    return {
        "city": city,
        "units": units,
        "current": current_out,
        "forecast_3d": forecast,
    }


# ── stock / crypto prices ─────────────────────────────────────────────────────

def stock_price(ticker: str) -> dict:
    """Fetch real-time price for a stock or crypto ticker via yfinance.

    Examples: AAPL, MSFT, BTC-USD, ETH-USD, FTSEMIB.MI
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance non installato. Esegui: uv add yfinance"}

    t = yf.Ticker(ticker.upper())
    try:
        info = t.fast_info
        hist = t.history(period="2d")
        if hist.empty:
            return {"error": f"Nessun dato per il ticker '{ticker}'"}

        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else last
        change = last - prev
        change_pct = (change / prev * 100) if prev else 0

        return {
            "ticker": ticker.upper(),
            "price": round(float(last), 4),
            "change": round(float(change), 4),
            "change_pct": round(float(change_pct), 2),
            "currency": getattr(info, "currency", "USD"),
            "market_cap": getattr(info, "market_cap", None),
            "volume": int(hist["Volume"].iloc[-1]),
            "exchange": getattr(info, "exchange", ""),
        }
    except Exception as e:
        return {"error": f"Errore recuperando dati per '{ticker}': {e}"}


# ── RSS / Atom feed ───────────────────────────────────────────────────────────

def rss_feed(url: str, max_items: int = 10) -> dict:
    """Parse an RSS or Atom feed and return the latest entries."""
    try:
        import feedparser
    except ImportError:
        return {"error": "feedparser non installato. Esegui: uv add feedparser"}

    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        return {"error": f"Feed non valido o non raggiungibile: {url}"}

    entries = []
    for e in feed.entries[:max_items]:
        entries.append({
            "title": e.get("title", ""),
            "link":  e.get("link", ""),
            "published": e.get("published", e.get("updated", "")),
            "summary": _strip_html(e.get("summary", e.get("description", "")))[:500],
        })

    return {
        "feed_title": feed.feed.get("title", url),
        "feed_url": url,
        "entries": entries,
        "total": len(entries),
    }


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


# ── PDF reader ────────────────────────────────────────────────────────────────

def pdf_read(source: str, max_pages: int = 20, max_chars: int = 12000) -> dict:
    """Extract text from a PDF file (local path or URL).

    source: absolute file path OR http(s) URL
    max_pages: max pages to extract (default 20)
    """
    try:
        import pdfplumber
    except ImportError:
        return {"error": "pdfplumber non installato. Esegui: uv add pdfplumber"}

    tmp_path = None
    try:
        if source.startswith("http://") or source.startswith("https://"):
            resp = requests.get(source, headers=_HEADERS, timeout=30)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(resp.content)
                tmp_path = f.name
            file_path = tmp_path
        else:
            file_path = str(Path(source).expanduser())
            if not Path(file_path).exists():
                return {"error": f"File non trovato: {source}"}

        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_read = min(max_pages, total_pages)
            text_parts = []
            for i, page in enumerate(pdf.pages[:pages_to_read]):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"--- Pagina {i+1} ---\n{page_text.strip()}")

            full_text = "\n\n".join(text_parts)
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + "\n\n[...troncato]"

            return {
                "source": source,
                "total_pages": total_pages,
                "pages_extracted": pages_to_read,
                "chars": len(full_text),
                "text": full_text,
            }
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


# ── YouTube transcript ────────────────────────────────────────────────────────

def youtube_transcript(url: str, lang: str = "it") -> dict:
    """Fetch the transcript of a YouTube video.

    url: full YouTube URL or video ID
    lang: preferred language code (default "it"); falls back to "en" if not available
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    except ImportError:
        return {"error": "youtube-transcript-api non installato. Esegui: uv add youtube-transcript-api"}

    video_id = _extract_video_id(url)
    if not video_id:
        return {"error": f"Impossibile estrarre video ID da: {url}"}

    api = YouTubeTranscriptApi()
    try:
        # fetch with language preference: preferred → English → any
        languages = [lang] if lang != "en" else []
        languages += ["en"]
        try:
            ft = api.fetch(video_id, languages=languages)
        except NoTranscriptFound:
            # fall back to first available language
            tl = api.list(video_id)
            first_lang = next(iter(tl)).language_code
            ft = api.fetch(video_id, languages=[first_lang])

        snippets = list(ft)
        language_used = ft.language_code

        text = " ".join(s.text for s in snippets)
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"  +", " ", text).strip()

        duration_s = int(snippets[-1].start + snippets[-1].duration) if snippets else 0
        duration_str = f"{duration_s // 60}m{duration_s % 60}s"

        return {
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "language": language_used,
            "duration": duration_str,
            "segments": len(snippets),
            "chars": len(text),
            "transcript": text[:12000] + ("\n\n[...troncato]" if len(text) > 12000 else ""),
        }

    except TranscriptsDisabled:
        return {"error": f"Trascrizioni disabilitate per questo video ({video_id})."}
    except Exception as e:
        return {"error": f"Errore recuperando trascrizione per '{video_id}': {e}"}


def _extract_video_id(url: str) -> str | None:
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url

    parsed = urlparse(url)
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        vid = qs.get("v", [None])[0]
        return vid
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/").split("?")[0] or None
    # shorts
    match = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", parsed.path)
    if match:
        return match.group(1)
    return None
