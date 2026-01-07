import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Config from Env
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@tradercopilot.com")


def send_recovery_email(to_email: str, reset_token: str):
    """
    Hybrid Sender (Priority Order):
    1. Mailgun API (HTTP) - Most Reliable
    2. SMTP - Standard
    3. Console - Dev / Fallback
    """
    import requests
    
    # Construct Link
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    subject = "TraderCopilot - Reset Your Password"
    
    btn_style = (
        "background:#2563eb;color:white;padding:10px 20px;"
        "text-decoration:none;border-radius:5px;"
    )

    body = f"""
    <h2>Password Reset Request</h2>
    <p>We received a request to reset your password for TraderCopilot.</p>
    <p>Click the link below to proceed:</p>
    <p>
        <a href="{reset_link}" style="{btn_style}">
            Reset Password
        </a>
    </p>
    <p>Or copy this URL:</p>
    <p>{reset_link}</p>
    <br>
    <p>If you did not request this, please ignore this email.</p>
    """

    # --- Mode 1: Mailgun API (HTTP) ---
    if MAILGUN_API_KEY and MAILGUN_DOMAIN:
        try:
            # Force EU Endpoint as verified
            mailgun_url = f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
            print(f"[EMAIL] 🚀 Sending via Mailgun API (EU) to {to_email}...")
            
            res = requests.post(
                mailgun_url,
                auth=("api", MAILGUN_API_KEY),
                data={
                    "from": f"TraderCopilot <postmaster@{MAILGUN_DOMAIN}>",
                    "to": to_email,
                    "subject": subject,
                    "html": body
                },
                timeout=10
            )
            if res.status_code == 200:
                print(f"[EMAIL] ✅ Sent via Mailgun API: {res.json().get('id', 'OK')}")
                return True
            else:
                print(f"[EMAIL] ⚠️ Mailgun API Error {res.status_code}: {res.text}")
                # Don't return False yet, try SMTP fallback? Or just fail logs.
        except Exception as e:
             print(f"[EMAIL] ❌ Mailgun API Exception: {e}")

    # --- Mode 2: SMTP ---
    if SMTP_SERVER:
        try:
            msg = MIMEMultipart()
            msg["From"] = FROM_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, to_email, msg.as_string())
                
            print(f"[EMAIL] ✅ Sent via SMTP to {to_email}")
            return True

        except Exception as e:
            print(f"[EMAIL] ❌ Failed to send SMTP: {e}")
            # Fallback to console

    # --- Mode 3: Console (Dev / Fallback) ---
    print("\n" + "="*60)
    print(f" [EMAIL DEBUG] To: {to_email}")
    print(f" [EMAIL DEBUG] Subj: {subject}")
    print(f" [EMAIL DEBUG] LINK: {reset_link}")
    print("="*60 + "\n")
    return True
