from google import genai
import os
import json
import re
from spam_model.spam_inference import predict_spam
from dotenv import load_dotenv
from ai.classifier import predict_email

# SAFE semantic import
try:
    from ai.semantic_memory import find_similar
except:
    def find_similar(subject, sender):
        return None

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "models/gemini-2.5-flash"


# --------------------------------------------------
# RULE ENGINE (ONLY OVERRIDES NOW)
# --------------------------------------------------

def rule_engine(sender, subject, body=""):

    s = sender.lower()
    sub = subject.lower()
    b = body.lower()

    # SECURITY OVERRIDE
    if any(word in sub for word in ["security", "verify", "alert", "password"]):
        return {"label": "security", "priority": "high"}

    # GITHUB NOTIFICATION
    if "github" in s:
        return {"label": "notification", "priority": "low"}

    # NEWSLETTER (unsubscribe signal strongest)
    if "unsubscribe" in b:
        return {"label": "newsletter", "priority": "low"}

    return None


# --------------------------------------------------
# PRIORITY RULES (LABEL-AWARE)
# --------------------------------------------------

def priority_rules(subject, sender, body, label):

    text = (subject + " " + body).lower()

    # FORCE LOW for passive categories
    if label in ["newsletter", "promotion", "job_alert", "event_invite"]:
        return "low"

    # HIGH urgency
    if any(word in text for word in [
        "urgent", "asap", "server down", "production", "immediately"
    ]):
        return "high"

    # MEDIUM
    if any(word in text for word in [
        "meeting", "review", "deadline", "call"
    ]):
        return "medium"

    return "low"


# --------------------------------------------------
# LABEL NORMALIZATION
# --------------------------------------------------

def normalize_label(label):

    if label == "event":
        return "event_invite"

    return label


# --------------------------------------------------
# MAIN PIPELINE (CLEAN)
# --------------------------------------------------

def process_inbox(email_list):

    results = []
    seen = set()

    for email in email_list:

        # -------------------------------
        # DEDUPLICATION
        # -------------------------------
        unique_id = email.get("id") or (email["subject"] + email["sender"])

        if unique_id in seen:
            continue
        seen.add(unique_id)

        # -------------------------------
        # ML CLASSIFIER
        # -------------------------------
        label = predict_email(
            email["subject"],
            email["sender"],
            email["body"]
        )

        # -------------------------------
        # RULE OVERRIDE (ALWAYS STRONG)
        # -------------------------------
        rule = rule_engine(
            email["sender"],
            email["subject"],
            email["body"]
        )

        if rule:
            label = rule["label"]

        # -------------------------------
        # PRIORITY
        # -------------------------------
        priority = priority_rules(
            email["subject"],
            email["sender"],
            email["body"],
            label
        )

        email["label"] = label
        email["priority"] = priority
        email["reply"] = ""

        results.append(email)

    return results



# --------------------------------------------------
# REPLY GENERATION (ONLY GEMINI USE)
# --------------------------------------------------

def generate_reply(email, tone):

    prompt = f"""
Write an email reply.

Tone: {tone}

EMAIL

From: {email["sender"]}
Subject: {email["subject"]}

Body:
{email["body"][:800]}

Write a clear reply. Do not include a signature.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text.strip()