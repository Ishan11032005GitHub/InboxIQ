import os

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN_FILE = "token.json"


def save_credentials(creds):
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


def load_credentials():
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


def get_client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret or not REDIRECT_URI:
        raise ValueError("Missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / REDIRECT_URI")

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [REDIRECT_URI],
        }
    }


def create_flow(state=None, code_verifier=None):
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
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


def exchange_code_for_credentials(code, state, code_verifier):
    flow = create_flow(state=state, code_verifier=code_verifier)
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_credentials(creds)
    return creds


def get_gmail_service(credentials):
    return build("gmail", "v1", credentials=credentials)
