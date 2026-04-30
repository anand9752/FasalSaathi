from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
import smtplib

from app.core.config import settings


def send_urgent_email(to_email: str, title: str, message: str, time: str) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        print("Email credentials not configured. Skipping email send.")
        return

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = "Urgent Alert from FasalSathi"

    safe_title = escape(title)
    safe_message = escape(message)
    safe_time = escape(time)
    frontend_url = escape(settings.frontend_url)

    html = f"""
    <html>
      <body>
        <h2>Urgent Alert from FasalSathi</h2>
        <p><strong>Title:</strong> {safe_title}</p>
        <p><strong>Message:</strong> {safe_message}</p>
        <p><strong>Time:</strong> {safe_time}</p>
        <p><a href="{frontend_url}" style="padding: 10px 15px; background-color: #22c55e; color: white; text-decoration: none; border-radius: 5px;">Open FasalSathi</a></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        print(f"Urgent email sent to {to_email}")
    except Exception as exc:
        print(f"Failed to send email: {exc}")
