import smtplib
from email.mime.text import MIMEText

# تنظیمات SMTP (پروڈاکشن: از env بخوان)
SMTP_HOST = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "no-reply@example.com"
SMTP_PASSWORD = "your_smtp_password"

FROM_EMAIL = "no-reply@example.com"
APP_NAME = "Auth Project"

def send_email(to_email: str, subject: str, html_body: str):
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

def build_reset_email(reset_link: str) -> str:
    return f"""
    <div>
      <h3>{APP_NAME} - Password Reset</h3>
      <p>برای ریست رمز عبور روی لینک زیر کلیک کن:</p>
      <p><a href="{reset_link}">{reset_link}</a></p>
      <p>این لینک مدت محدودی اعتبار دارد.</p>
    </div>
    """

def build_verification_email(verify_link: str) -> str:
    return f"""
    <div>
      <h3>{APP_NAME} - Email Verification</h3>
      <p>برای تأیید ایمیل روی لینک زیر کلیک کن:</p>
      <p><a href="{verify_link}">{verify_link}</a></p>
      <p>این لینک مدت محدودی اعتبار دارد.</p>
    </div>
    """
