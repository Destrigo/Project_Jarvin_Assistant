"""Web tools: search, fetch, scrape."""
import os
import re
from urllib.parse import urlparse, urljoin

import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
_TIMEOUT = 15


# ── web search ─────────────────────────────────────────────────────────────────

def search(query: str, max_results: int = 8) -> dict:
    """Search the web. Uses Brave API if BRAVE_SEARCH_API_KEY is set, else DuckDuckGo."""
    brave_key = os.getenv("BRAVE_SEARCH_API_KEY", "")
    if brave_key:
        return _brave_search(query, max_results, brave_key)
    return _ddg_search(query, max_results)


def _brave_search(query: str, max_results: int, api_key: str) -> dict:
    resp = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": max_results},
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    results = [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")}
        for r in data.get("web", {}).get("results", [])
    ]
    return {"engine": "brave", "query": query, "results": results}


def _ddg_search(query: str, max_results: int) -> dict:
    from duckduckgo_search import DDGS
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url":   r.get("href", ""),
                "snippet": r.get("body", ""),
            })
    return {"engine": "duckduckgo", "query": query, "results": results}


# ── web fetch ──────────────────────────────────────────────────────────────────

def fetch(url: str, max_chars: int = 8000) -> dict:
    """Fetch a URL and return clean readable text (HTML → markdown)."""
    resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")

    if "text/html" not in content_type and "application/xhtml" not in content_type:
        # plain text / JSON / other
        return {
            "url": url,
            "content_type": content_type,
            "text": resp.text[:max_chars],
        }

    try:
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        h.ignore_tables = False
        text = h.handle(resp.text)
    except ImportError:
        # fallback: strip tags with regex
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s{3,}", "\n\n", text)

    # trim to max_chars, preferring sentence boundaries
    if len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0] + "\n\n[...troncato]"

    return {"url": url, "text": text, "chars": len(text)}


# ── web scrape ─────────────────────────────────────────────────────────────────

def scrape(url: str, selector: str = "", extract: str = "text") -> dict:
    """Scrape structured data from a URL.

    Args:
        url:      target URL
        selector: CSS selector (e.g. "table", "article p", "#main-content")
                  leave empty for full body
        extract:  "text"   → plain text of selected elements
                  "links"  → all <a href> found
                  "table"  → parse first <table> as list of dicts
                  "list"   → all <li> text items
                  "html"   → raw HTML of selected elements
    """
    from bs4 import BeautifulSoup

    resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # remove noisy elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    elements = soup.select(selector) if selector else [soup.body or soup]

    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    if extract == "links":
        links = []
        for el in elements:
            for a in el.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = urljoin(base, href)
                links.append({"text": a.get_text(strip=True), "url": href})
        return {"url": url, "selector": selector, "links": links[:100]}

    if extract == "table":
        tables = []
        for el in elements:
            for table in el.find_all("table"):
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                rows = []
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if cells:
                        row = dict(zip(headers, cells)) if headers else cells
                        rows.append(row)
                if rows:
                    tables.append(rows)
        return {"url": url, "selector": selector, "tables": tables}

    if extract == "list":
        items = []
        for el in elements:
            for li in el.find_all("li"):
                t = li.get_text(strip=True)
                if t:
                    items.append(t)
        return {"url": url, "selector": selector, "items": items[:200]}

    if extract == "html":
        return {"url": url, "selector": selector, "html": "\n".join(str(el) for el in elements)[:8000]}

    # default: text
    parts = []
    for el in elements:
        t = el.get_text(separator="\n", strip=True)
        if t:
            parts.append(t)
    text = "\n\n".join(parts)[:8000]
    return {"url": url, "selector": selector, "text": text}
