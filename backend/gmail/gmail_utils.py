import base64
import re
from email.mime.text import MIMEText
from html import unescape
from typing import Any, Dict, List


def _decode_base64(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _html_to_text(html: str) -> str:
    if not html:
        return ""

    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p>", "\n", html)
    html = re.sub(r"(?i)</div>", "\n", html)
    html = re.sub(r"(?i)</li>", "\n", html)
    html = re.sub(r"(?i)</tr>", "\n", html)
    html = re.sub(r"(?i)</h[1-6]>", "\n", html)

    html = re.sub(r"(?s)<.*?>", " ", html)
    text = unescape(html)

    text = re.sub(r"\r", "", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _extract_body_from_payload(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""

    plain_text = None
    html_text = None

    def walk(part: Dict[str, Any]):
        nonlocal plain_text, html_text

        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")

        if mime_type == "text/plain" and body_data and not plain_text:
            decoded = _decode_base64(body_data)
            if decoded.strip():
                plain_text = decoded

        elif mime_type == "text/html" and body_data and not html_text:
            decoded = _decode_base64(body_data)
            if decoded.strip():
                html_text = decoded

        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)

    if plain_text and plain_text.strip():
        return plain_text.strip()

    if html_text and html_text.strip():
        return _html_to_text(html_text)

    body_data = payload.get("body", {}).get("data")
    if body_data:
        decoded = _decode_base64(body_data)
        if decoded.strip():
            if "<html" in decoded.lower() or "<div" in decoded.lower():
                return _html_to_text(decoded)
            return decoded.strip()

    return ""


def get_unread_emails(service, max_results=5, page_token=None):
    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'UNREAD'],
        maxResults=max_results,
        pageToken=page_token
    ).execute()

    messages = results.get('messages', [])
    next_page_token = results.get('nextPageToken')

    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        headers = msg_data['payload'].get('headers', [])

        subject = ""
        sender = ""

        for h in headers:
            if h['name'] == 'Subject':
                subject = h['value']
            elif h['name'] == 'From':
                sender = h['value']

        body = ""

        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        import base64
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
        else:
            data = msg_data['payload']['body'].get('data')
            if data:
                import base64
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        emails.append({
            "id": msg['id'],
            "subject": subject,
            "sender": sender,
            "body": body[:2000]
        })

    return {
        "emails": emails,
        "next_page_token": next_page_token
    }


def send_email(service, to: str, subject: str, body: str) -> None:
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()
