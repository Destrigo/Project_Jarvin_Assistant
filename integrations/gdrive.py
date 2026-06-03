"""Google Drive integration — list and read files."""
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from integrations.google_auth import get_credentials

_GDOC_MIME   = "application/vnd.google-apps.document"
_GSHEET_MIME = "application/vnd.google-apps.spreadsheet"
_GSLIDE_MIME = "application/vnd.google-apps.presentation"


def _service():
    return build("drive", "v3", credentials=get_credentials())


def drive_list(folder_id: str = "root", max_results: int = 20,
               query: str = "") -> dict:
    """List files in Google Drive.

    folder_id: Drive folder ID or 'root' for My Drive root.
    query: extra Drive query string, e.g. "name contains 'budget'"
    """
    svc = _service()
    q_parts = [f"'{folder_id}' in parents", "trashed = false"]
    if query:
        q_parts.append(query)
    q = " and ".join(q_parts)

    resp = svc.files().list(
        q=q,
        pageSize=max_results,
        fields="files(id, name, mimeType, modifiedTime, size, parents)",
        orderBy="modifiedTime desc",
    ).execute()

    files = []
    for f in resp.get("files", []):
        files.append({
            "id":       f["id"],
            "name":     f["name"],
            "type":     _label(f["mimeType"]),
            "mime":     f["mimeType"],
            "modified": f.get("modifiedTime", ""),
            "size_kb":  round(int(f.get("size", 0)) / 1024, 1),
        })

    return {"folder_id": folder_id, "files": files, "count": len(files)}


def drive_read(file_id: str, max_chars: int = 12000) -> dict:
    """Read the text content of a Drive file.

    Supports: Google Docs (exported as text), plain text files,
              Google Sheets (exported as CSV), PDFs.
    Returns metadata for binary files it can't read.
    """
    svc = _service()
    meta = svc.files().get(
        fileId=file_id, fields="id,name,mimeType,modifiedTime,size"
    ).execute()

    name = meta["name"]
    mime = meta["mimeType"]

    # Google Docs → plain text export
    if mime == _GDOC_MIME:
        content = svc.files().export(
            fileId=file_id, mimeType="text/plain"
        ).execute()
        text = content.decode("utf-8", errors="replace")[:max_chars]
        return {"id": file_id, "name": name, "type": "Google Doc", "text": text, "chars": len(text)}

    # Google Sheets → CSV export
    if mime == _GSHEET_MIME:
        content = svc.files().export(
            fileId=file_id, mimeType="text/csv"
        ).execute()
        text = content.decode("utf-8", errors="replace")[:max_chars]
        return {"id": file_id, "name": name, "type": "Google Sheet (CSV)", "text": text, "chars": len(text)}

    # Google Slides → plain text
    if mime == _GSLIDE_MIME:
        content = svc.files().export(
            fileId=file_id, mimeType="text/plain"
        ).execute()
        text = content.decode("utf-8", errors="replace")[:max_chars]
        return {"id": file_id, "name": name, "type": "Google Slides", "text": text, "chars": len(text)}

    # plain text / markdown / JSON / CSV
    if mime.startswith("text/") or mime in ("application/json",):
        fh = io.BytesIO()
        req = svc.files().get_media(fileId=file_id)
        MediaIoBaseDownload(fh, req).next_chunk()
        text = fh.getvalue().decode("utf-8", errors="replace")[:max_chars]
        return {"id": file_id, "name": name, "type": mime, "text": text, "chars": len(text)}

    # binary / unsupported
    return {
        "id": file_id, "name": name, "type": mime,
        "error": "Tipo di file non leggibile come testo. Usa un Google Doc o file di testo.",
        "size_kb": round(int(meta.get("size", 0)) / 1024, 1),
    }


def _label(mime: str) -> str:
    return {
        _GDOC_MIME:   "Google Doc",
        _GSHEET_MIME: "Google Sheet",
        _GSLIDE_MIME: "Google Slides",
        "application/vnd.google-apps.folder": "Folder",
        "application/pdf": "PDF",
        "text/plain": "Text",
        "application/json": "JSON",
    }.get(mime, mime.split("/")[-1])
