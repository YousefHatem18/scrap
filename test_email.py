import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

sender_email = os.environ["SENDER_EMAIL"]
app_password = os.environ["APP_PASSWORD"]
receiver_email = os.environ["RECEIVER_EMAIL"]

msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = "Test Email"
msg.attach(MIMEText("لو وصلك ده، الإيميل شغال تمام", "plain", "utf-8"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(sender_email, app_password)
    server.send_message(msg)

print("✅ Email Sent")
