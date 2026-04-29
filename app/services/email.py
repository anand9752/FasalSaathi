import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_urgent_email(to_email: str, title: str, message: str, time: str):
    # Retrieve credentials from environment variables
    # Defaulting to placeholders so it doesn't break if not configured
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    
    if not smtp_user or not smtp_password:
        print("Email credentials not configured. Skipping email send.")
        return

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = f"🚨 Urgent Alert from FasalSathi"

    html = f"""
    <html>
      <body>
        <h2>🚨 Urgent Alert from FasalSathi</h2>
        <p><strong>Title:</strong> {title}</p>
        <p><strong>Message:</strong> {message}</p>
        <p><strong>Time:</strong> {time}</p>
        <p><a href="http://localhost:5173" style="padding: 10px 15px; background-color: #22c55e; color: white; text-decoration: none; border-radius: 5px;">Open FasalSathi</a></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Urgent email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
