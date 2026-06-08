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

_TOKEN_PATH  = Path(os.getenv("GOOGLE_TOKEN_FILE",   "config/google_token.json"))
_SECRET_PATH = Path(os.getenv("GOOGLE_CLIENT_SECRET_FILE", "config/google_client_secret.json"))


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
                "Carica google_token.json e google_client_secret.json come Secret Files su Render "
                "(Settings → Secret Files → /etc/secrets/google_token.json)."
            )
        _TOKEN_PATH.parent.mkdir(exist_ok=True)
        _TOKEN_PATH.write_text(creds.to_json())
    return creds
