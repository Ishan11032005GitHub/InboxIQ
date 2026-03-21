from gmail_service import authenticate_gmail, get_unread_emails, mark_as_read
from gemini_agent import analyze_email
from review_loop import review_draft


def main():

    service = authenticate_gmail()

    emails = get_unread_emails(service)

    print("Unread emails:", len(emails))

    for email in emails[:3]:

        ai_response = analyze_email(email)

        review = review_draft(email, ai_response)

        if review:

            print("\nReply approved")
            print(review)

            # sending reply logic can be added here

        mark_as_read(service, email["id"])


if __name__ == "__main__":
    main()