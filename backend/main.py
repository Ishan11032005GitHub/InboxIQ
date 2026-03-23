from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from backend.auth.google_auth import (
    get_authorization_data,
    exchange_code_for_credentials,
    get_gmail_service,
    load_credentials
)

from backend.gmail.gmail_utils import get_unread_emails, send_email
from backend.ai.gemini_utils import process_inbox, generate_reply
from backend.ai.classifier import predict_with_confidence
from backend.memory.feedback_store import save_feedback
from fastapi import Request, HTTPException, Cookie
from fastapi.responses import RedirectResponse

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
oauth_store = {}   # state -> code_verifier
email_cache = {}   # id -> email


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
        samesite="lax",
        max_age=600,
        path="/"
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
# GET EMAILS
# -----------------------------
@app.get("/emails")
def get_emails():

    creds = load_credentials()
    if not creds:
        raise HTTPException(401, "Not authenticated")

    service = get_gmail_service(creds)

    emails = get_unread_emails(service)
    emails = process_inbox(emails)

    result = []

    for e in emails:
        label, conf = predict_with_confidence(
            e["subject"],
            e["sender"],
            e["body"]
        )

        e["confidence"] = conf

        email_cache[e["id"]] = e
        result.append(e)

    return result


# -----------------------------
# GENERATE REPLY
# -----------------------------
@app.post("/generate-reply")
async def generate(request: Request):

    data = await request.json()
    email_id = data.get("id")

    if email_id not in email_cache:
        raise HTTPException(404, "Email not found")

    email = email_cache[email_id]

    reply = generate_reply(email, "professional")

    return {"reply": reply}


# -----------------------------
# SEND EMAIL
# -----------------------------
@app.post("/send-email")
async def send(request: Request):

    creds = load_credentials()
    if not creds:
        raise HTTPException(401, "Not authenticated")

    service = get_gmail_service(creds)

    data = await request.json()

    send_email(
        service,
        data["to"],
        data["subject"],
        data["body"]
    )

    return {"status": "sent"}

@app.get("/auth/status")
def auth_status():
    creds = load_credentials()
    return {"authenticated": creds is not None}


@app.post("/auth/logout")
def logout():
    import os

    token_file = "token.json"
    if os.path.exists(token_file):
        os.remove(token_file)

    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie("code_verifier", path="/")
    return response

# -----------------------------
# SAVE FEEDBACK
# -----------------------------
@app.post("/save-feedback")
async def feedback(request: Request):

    data = await request.json()
    email_id = data.get("id")
    label = data.get("label")

    if email_id not in email_cache:
        raise HTTPException(404, "Email not found")

    save_feedback(email_cache[email_id], label)

    return {"status": "saved"}


@app.get("/")
def root():
    return {"status": "ok", "message": "Welcome to Inbox IQ API"}