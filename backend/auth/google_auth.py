import json
import os
from typing import Optional
from urllib.parse import urlencode

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://inboxiq-edvu.onrender.com/auth/callback")
TOKEN_FILE = "token.json"


def save_credentials(creds: Credentials) -> None:
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


def load_credentials() -> Optional[Credentials]:
    if not os.path.exists(TOKEN_FILE):
        return None

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
        except Exception:
            return None

    return creds


def get_client_config() -> dict:
    client_secret_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
    if not client_secret_json:
        raise ValueError("Missing GOOGLE_CLIENT_SECRET_JSON environment variable.")

    data = json.loads(client_secret_json)
    if "web" not in data:
        raise ValueError("GOOGLE_CLIENT_SECRET_JSON must contain top-level 'web' key.")

    return data


def create_flow(state: Optional[str] = None, code_verifier: Optional[str] = None) -> Flow:
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    if state:
        flow.oauth2session.state = state

    if code_verifier:
        flow.code_verifier = code_verifier

    return flow


def get_authorization_data():
    flow = create_flow()

    auth_url, state = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )

    return {
        "auth_url": auth_url,
        "state": state,
        "code_verifier": flow.code_verifier,
    }


def exchange_code_for_credentials(code: str, state: Optional[str], code_verifier: str) -> Credentials:
    flow = create_flow(state=state, code_verifier=code_verifier)
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_credentials(creds)
    return creds


def get_gmail_service(credentials: Credentials):
    return build("gmail", "v1", credentials=credentials)


def get_saved_service():
    creds = load_credentials()
    if not creds:
        raise Exception("Login required first.")
    return build("gmail", "v1", credentials=creds)
