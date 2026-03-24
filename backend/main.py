import os
import uvicorn

from fastapi import FastAPI, Request, HTTPException, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.auth.google_auth import (
    get_authorization_data,
    exchange_code_for_credentials,
    get_gmail_service,
    load_credentials,
)
from backend.gmail.gmail_utils import get_unread_emails, send_email
from backend.ai.gemini_utils import process_inbox, generate_reply
from backend.memory.feedback_store import save_feedback

app = FastAPI()

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://inbox-iq-xi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# TEMP STORAGE
# -----------------------------
email_cache = {} # id -> email


# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Welcome to InboxIQ API"}


# -----------------------------
# AUTH STATUS
# -----------------------------
@app.get("/auth/status")
def auth_status():
    creds = load_credentials()
    return {"authenticated": creds is not None}


# -----------------------------
# AUTH LOGIN
# -----------------------------
@app.get("/auth/login")
def login():
    data = get_authorization_data()

    response = RedirectResponse(url=data["auth_url"], status_code=302)
    response.set_cookie(
        key="code_verifier",
        value=data["code_verifier"],
        httponly=True,
        secure=True,
        samesite="none",
        max_age=600,
        path="/",
    )
    return response


# -----------------------------
# AUTH CALLBACK
# -----------------------------
@app.get("/auth/callback")
def callback(request: Request, code_verifier: str = Cookie(default=None)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    if not code_verifier:
        raise HTTPException(status_code=400, detail="Missing code_verifier cookie")

    try:
        exchange_code_for_credentials(code, state, code_verifier)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")

    frontend_url = os.getenv("FRONTEND_URL")
    if not frontend_url:
        raise HTTPException(status_code=500, detail="FRONTEND_URL not set")

    response = RedirectResponse(frontend_url, status_code=302)
    response.delete_cookie("code_verifier", path="/")
    return response


# -----------------------------
# AUTH LOGOUT
# -----------------------------
@app.post("/auth/logout")
def logout():
    token_file = os.path.join(os.path.dirname(__file__), "auth", "token.json")

    if os.path.exists(token_file):
        os.remove(token_file)

    email_cache.clear()

    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie("code_verifier", path="/")
    return response


# -----------------------------
# GET EMAILS
# -----------------------------
@app.get("/emails")
def get_emails(limit: int = 5, page_token: str | None = None):
    creds = load_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        service = get_gmail_service(creds)

        payload = get_unread_emails(
            service,
            max_results=limit,
            page_token=page_token
        )

        emails = payload["emails"]
        next_page_token = payload.get("next_page_token")

        emails = process_inbox(emails)

        result = []
        for email in emails:
            email_cache[email["id"]] = email
            result.append(email)

        return {
            "emails": result,
            "next_page_token": next_page_token
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load emails: {str(e)}")


# -----------------------------
# GENERATE REPLY
# -----------------------------
@app.post("/generate-reply")
async def generate(request: Request):
    data = await request.json()
    email_id = data.get("id")

    if not email_id or email_id not in email_cache:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        email = email_cache[email_id]
        reply = generate_reply(email, "professional")
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reply generation failed: {str(e)}")


# -----------------------------
# SEND EMAIL
# -----------------------------
@app.post("/send-email")
async def send(request: Request):
    creds = load_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = await request.json()

    to = data.get("to", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()

    if not to or not subject or not body:
        raise HTTPException(status_code=400, detail="Missing to / subject / body")

    try:
        service = get_gmail_service(creds)
        send_email(service, to, subject, body)
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Send failed: {str(e)}")


# -----------------------------
# SAVE FEEDBACK
# -----------------------------
@app.post("/save-feedback")
async def feedback(request: Request):
    data = await request.json()
    email_id = data.get("id")
    label = data.get("label")

    if not email_id or email_id not in email_cache:
        raise HTTPException(status_code=404, detail="Email not found")

    if not label:
        raise HTTPException(status_code=400, detail="Missing label")

    try:
        save_feedback(email_cache[email_id], label)
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback save failed: {str(e)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
