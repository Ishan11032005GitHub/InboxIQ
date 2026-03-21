import json
import os
import tempfile

import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# IMPORTANT:
# This must exactly match one of the authorized redirect URIs
# in your Google Cloud OAuth client.
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://inboxiq-edvu.onrender.com")
TOKEN_FILE = "token.json"


def save_credentials(creds):
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


def load_credentials():
    if os.path.exists(TOKEN_FILE):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_credentials(creds)
            except Exception:
                return None

        return creds

    return None


def _get_client_secrets_file():
    client_secret_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")

    if not client_secret_json:
        raise ValueError("Missing GOOGLE_CLIENT_SECRET_JSON environment variable.")

    data = json.loads(client_secret_json)

    # Validate expected structure early
    if "web" not in data:
        raise ValueError("GOOGLE_CLIENT_SECRET_JSON must contain a top-level 'web' key.")

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, tmp)
    tmp.flush()
    tmp.close()

    return tmp.name


def login():
    # 1. Reuse saved credentials if valid
    creds = load_credentials()
    if creds and creds.valid:
        return creds

    query_params = st.query_params
    client_secrets_file = _get_client_secrets_file()

    # 2. Handle callback
    if "code" in query_params:
        if "code_verifier" not in st.session_state:
            st.warning("Session lost. Restarting login...")
            st.query_params.clear()
            st.rerun()

        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )

        flow.code_verifier = st.session_state["code_verifier"]
        flow.fetch_token(code=query_params["code"])

        credentials = flow.credentials
        save_credentials(credentials)

        st.session_state["credentials"] = credentials
        st.session_state.pop("code_verifier", None)
        st.query_params.clear()

        st.success("✅ Login successful")
        st.rerun()

    # 3. Start login flow
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )

    st.session_state["code_verifier"] = flow.code_verifier

    st.markdown(f"### 🔐 [Login with Google]({auth_url})")
    st.stop()


def get_gmail_service(credentials):
    return build("gmail", "v1", credentials=credentials)


def get_saved_service():
    creds = load_credentials()
    if not creds:
        raise Exception("Login required first.")
    return build("gmail", "v1", credentials=creds)
