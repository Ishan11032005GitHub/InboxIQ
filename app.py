import streamlit as st
from datetime import datetime, timedelta
from gmail.gmail_utils import get_unread_emails, send_email
import subprocess

from automation.scheduler import schedule_email
from ai.gemini_utils import process_inbox, generate_reply
from ai.classifier import predict_with_confidence
from memory.feedback_store import save_feedback
from auth.google_auth import login, get_gmail_service

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="AI Gmail Assistant", layout="wide")
st.title("AI Gmail Assistant")

# ---------------------------------------------------
# AUTH (FIXED)
# ---------------------------------------------------
if "credentials" not in st.session_state:
    st.session_state["credentials"] = login()

credentials = st.session_state["credentials"]
service = get_gmail_service(credentials)

# ---------------------------------------------------
# LOAD EMAILS (SAFE CACHE)
# ---------------------------------------------------
@st.cache_data(ttl=60)
def load_emails(token):
    svc = get_gmail_service(credentials)
    return get_unread_emails(svc)

emails = load_emails(credentials.token)

# ---------------------------------------------------
# COMPOSE EMAIL
# ---------------------------------------------------
st.header("Compose Email")

compose_to = st.text_input("To")
compose_subject = st.text_input("Subject")
compose_body = st.text_area("Email Body", height=200)

if st.button("Send Email"):
    if compose_to and compose_subject and compose_body:
        try:
            send_email(service, compose_to, compose_subject, compose_body)
            st.success("Email Sent")
        except Exception as e:
            st.error(f"Send failed: {str(e)}")
    else:
        st.warning("Fill all fields")

st.divider()

# ---------------------------------------------------
# CLASSIFICATION
# ---------------------------------------------------
classified_emails = process_inbox(emails)

# ---------------------------------------------------
# INBOX
# ---------------------------------------------------
if not classified_emails:
    st.info("No unread emails found.")
else:
    for email in classified_emails:

        reply_key = f"reply_{email['id']}"
        feedback_key = f"feedback_{email['id']}"

        label, confidence = predict_with_confidence(
            email["subject"],
            email["sender"],
            email["body"]
        )

        st.subheader(email["subject"])
        st.write("From:", email["sender"])
        st.write("Label:", email.get("label"))
        st.write("Confidence:", round(confidence, 2))

        # 🔥 SHOW BODY (IMPORTANT)
        with st.expander("View Email Body"):
            st.write(email["body"][:1000])

        # -------------------------
        # FEEDBACK
        # -------------------------
        if confidence < 0.6:
            correct_label = st.selectbox(
                "Correct Label",
                [
                    "job_alert", "promotion", "newsletter",
                    "event_invite", "notification",
                    "work", "security", "general"
                ],
                key=feedback_key
            )

            if st.button("Save Feedback", key=f"save_{email['id']}"):
                save_feedback(email, correct_label)

                # ⚠️ FIX: prevent multiple retrain spam
                if "retraining" not in st.session_state:
                    st.session_state["retraining"] = True
                    subprocess.Popen(["python", "retrain.py"])

                st.success("Feedback saved. Model updating...")

        # -------------------------
        # REPLY
        # -------------------------
        if reply_key not in st.session_state:
            st.session_state[reply_key] = ""

        st.text_area("Reply", key=reply_key)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generate Reply", key=email["id"] + "gen"):
                reply = generate_reply(email, "professional")
                st.session_state[reply_key] = reply
                st.rerun()

        with col2:
            if st.button("Send Reply", key=email["id"] + "send"):
                send_email(
                    service,
                    email["sender"],
                    email["subject"],
                    st.session_state[reply_key]
                )
                st.success("Sent")

        st.divider()
