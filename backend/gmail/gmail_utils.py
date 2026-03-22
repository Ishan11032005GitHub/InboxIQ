import base64
from email.mime.text import MIMEText
from typing import Any, Dict, List


def _extract_body(payload: Dict[str, Any]) -> str:
    body = ""

    if not payload:
        return body

    if payload.get("body", {}).get("data"):
        try:
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    for part in payload.get("parts", []) or []:
        mime_type = part.get("mimeType", "")
        data = part.get("body", {}).get("data")

        if mime_type == "text/plain" and data:
            try:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            except Exception:
                continue

        nested_parts = part.get("parts", [])
        if nested_parts:
            nested_body = _extract_body(part)
            if nested_body:
                return nested_body

    return body


def get_unread_emails(service, max_results: int = 5) -> List[Dict[str, str]]:
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="is:unread",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = message.get("payload", {}).get("headers", [])

        subject = ""
        sender = ""

        for h in headers:
            name = h.get("name", "")
            value = h.get("value", "")
            if name == "Subject":
                subject = value
            elif name == "From":
                sender = value

        body = _extract_body(message.get("payload", {}))

        emails.append({
            "id": msg["id"],
            "threadId": message.get("threadId", ""),
            "subject": subject,
            "sender": sender,
            "body": body
        })

    return emails


def send_email(service, to: str, subject: str, body: str) -> None:
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()
