from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import random, os

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_USERNAME"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False
)

def generate_code() -> str:
    return str(random.randint(100000, 999999))

async def send_verification_email(email: str, code: str):
    message = MessageSchema(
        subject="Verify your Agop account",
        recipients=[email],
        body=f"Your verification code is: {code}\n\nExpires in 10 minutes.",
        subtype="plain"
    )
    await FastMail(conf).send_message(message)