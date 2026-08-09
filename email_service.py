import smtplib
import os

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_otp_email(receiver_email, otp):

    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    message = EmailMessage()

    message["Subject"] = "ResumeAI Password Reset Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.set_content(
        f"""
Hello,

Your ResumeAI password reset code is:

{otp}

This code will expire in 10 minutes.

If you did not request a password reset,
you can ignore this email.

Regards,
ResumeAI Team
"""
    )

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            sender_email,
            sender_password
        )

        smtp.send_message(message)