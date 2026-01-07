import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Config from Env
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@tradercopilot.com")

def send_recovery_email(to_email: str, reset_token: str):
    """
    Hybrid Sender:
    1. If SMTP_SERVER is set -> Sends real email.
    2. Else -> Prints recovery link to Console (Logs).
    """
    
    # Construct Link (adjust frontend URL as needed)
    # Defaulting to localhost for dev, but can be env var
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    subject = "TraderCopilot - Reset Your Password"
    body = f"""
    <h2>Password Reset Request</h2>
    <p>We received a request to reset your password for TraderCopilot.</p>
    <p>Click the link below to proceed:</p>
    <p>
        <a href="{reset_link}" style="background:#2563eb;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
            Reset Password
        </a>
    </p>
    <p>Or copy this URL:</p>
    <p>{reset_link}</p>
    <br>
    <p>If you did not request this, please ignore this email.</p>
    """

    # --- Mode 1: Console (Dev / No Config) ---
    if not SMTP_SERVER:
        print("\n" + "="*60)
        print(f" [EMAIL DEBUG] To: {to_email}")
        print(f" [EMAIL DEBUG] Subj: {subject}")
        print(f" [EMAIL DEBUG] LINK: {reset_link}")
        print("="*60 + "\n")
        return True

    # --- Mode 2: SMTP (Prod) ---
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
            
        print(f"[EMAIL] ✅ Sent recovery email to {to_email}")
        return True

    except Exception as e:
        print(f"[EMAIL] ❌ Failed to send SMTP: {e}")
        # Fallback to console so user isn't locked out in case of SMTP flakiness
        print(f" [FALLBACK LINK]: {reset_link}")
        return False
