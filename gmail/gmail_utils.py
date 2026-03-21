import base64
from email.mime.text import MIMEText


def get_unread_emails(service):

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="is:unread",
        maxResults=5
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for msg in messages:

        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = message["payload"]["headers"]

        subject = ""
        sender = ""

        for h in headers:
            if h["name"] == "Subject":
                subject = h["value"]
            if h["name"] == "From":
                sender = h["value"]

        body = ""

        parts = message["payload"].get("parts", [])

        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode()

        emails.append({
            "id": msg["id"],
            "threadId": message["threadId"],
            "subject": subject,
            "sender": sender,
            "body": body
        })

    return emails


def send_email(service, to, subject, body):

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()