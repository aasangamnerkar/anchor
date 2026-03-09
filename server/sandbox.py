import smtplib
import imaplib
import email
import time
import uuid
from email.message import EmailMessage

# -----------------------------
# CONFIG - need @anchor email set up
# -----------------------------

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

IMAP_SERVER = "imap.gmail.com"

EMAIL_ADDRESS = "you@gmail.com"
EMAIL_PASSWORD = "your_app_password"

RECIPIENT = "recipient@example.com"

CHECK_INTERVAL = 10  # seconds


def send_email():
    msg = EmailMessage()

    unique_id = str(uuid.uuid4())[:8]
    subject = f"Test Message {unique_id}"

    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECIPIENT

    msg.set_content(
        f"""
Hello,

This is a test message.

Please reply so the script can detect it.

ID: {unique_id}
"""
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print("Email sent.")
    return unique_id



def main():
    unique_id = send_email()

if __name__ == "__main__":
    main()