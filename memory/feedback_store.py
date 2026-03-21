import json
import os
import hashlib

FEEDBACK_FILE = "data/feedback.json"


def _hash_email(email):
    text = f"{email['subject']}_{email['sender']}_{email['body']}"
    return hashlib.md5(text.encode()).hexdigest()


def load_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return []

    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_feedback(email, correct_label):

    data = load_feedback()

    email_id = _hash_email(email)

    # avoid duplicates
    for item in data:
        if item["id"] == email_id:
            item["label"] = correct_label
            break
    else:
        data.append({
            "id": email_id,
            "subject": email["subject"],
            "sender": email["sender"],
            "body": email["body"],
            "label": correct_label
        })

    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)