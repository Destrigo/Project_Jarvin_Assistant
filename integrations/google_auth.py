"""Single OAuth2 auth module for all Google services.

Both Gmail and Calendar share the same token file with combined scopes.
Import this instead of calling _service() in each integration.
"""
import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/tasks",
]

def _default_path(env_var: str, fname: str) -> Path:
    jarvis_home = os.getenv("JARVIS_HOME")
    if jarvis_home:
        return Path(jarvis_home) / fname
    return Path(os.getenv(env_var, f"config/{fname}"))

_TOKEN_PATH  = _default_path("GOOGLE_TOKEN_FILE",          "google_token.json")
_SECRET_PATH = _default_path("GOOGLE_CLIENT_SECRET_FILE",  "google_client_secret.json")


def get_credentials() -> Credentials:
    creds = None
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "Credenziali Google mancanti o scadute sul server. "
                "Imposta GOOGLE_TOKEN_JSON e GOOGLE_CLIENT_SECRET_JSON nelle env var di Render "
                "con il contenuto JSON dei rispettivi file."
            )
        _TOKEN_PATH.parent.mkdir(exist_ok=True)
        _TOKEN_PATH.write_text(creds.to_json())
    return creds
