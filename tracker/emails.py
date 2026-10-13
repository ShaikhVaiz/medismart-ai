import logging
import resend
from django.conf import settings

logger = logging.getLogger(__name__)


def send_password_reset_otp_email(user, otp_code):
    """
    Sends a 6-digit password reset OTP email using the Resend API.
    If RESEND_API_KEY is not configured yet, logs the OTP to the console
    so development and local testing remain unblocked.
    """
    api_key = getattr(settings, "RESEND_API_KEY", "")
    from_email = getattr(settings, "RESEND_FROM_EMAIL", "onboarding@resend.dev")

    if not user.email:
        return False, "This account does not have an email address associated with it."

    subject = f"MediSmart AI — Your Password Reset Code: {otp_code}"
    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; border: 1px solid #e3ebee; border-radius: 14px; background: #ffffff;">
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; background: #d9f3ed; color: #0f766e; padding: 8px 14px; border-radius: 10px; font-weight: 800; font-size: 18px;">
                ✚ MediSmart <span style="font-weight: 400;">AI</span>
            </div>
        </div>
        <h2 style="color: #122b3a; margin-top: 0; font-size: 20px;">Password Reset Request</h2>
        <p style="color: #556977; font-size: 14px; line-height: 1.6;">Hello <strong>{user.username}</strong>,</p>
        <p style="color: #556977; font-size: 14px; line-height: 1.6;">Use the 6-digit verification code below to reset your MediSmart AI account password:</p>
        <div style="background: #f0fdf9; border: 1px solid #ccfbf1; border-radius: 10px; padding: 20px; text-align: center; margin: 24px 0;">
            <span style="font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #0f766e; font-family: monospace;">{otp_code}</span>
        </div>
        <p style="color: #71818c; font-size: 12px; line-height: 1.5;">This code will expire in <strong>10 minutes</strong>. If you did not request a password reset, you can safely ignore this email.</p>
        <hr style="border: 0; border-top: 1px solid #eef2f4; margin: 24px 0;">
        <p style="color: #94a3b8; font-size: 11px; text-align: center; margin: 0;">MediSmart AI · Personal Medicine Reminder & Reorder</p>
    </div>
    """

    if not api_key:
        print(f"\n=======================================================")
        print(f"[DEMO / DEV EMAIL] Password Reset OTP for {user.email}: {otp_code}")
        print(f"=======================================================\n")
        return True, "A 6-digit OTP code has been generated. (Note: RESEND_API_KEY is not set in .env, so the code was printed to the terminal console)."

    try:
        resend.api_key = api_key
        params: resend.Emails.SendParams = {
            "from": from_email,
            "to": [user.email],
            "subject": subject,
            "html": html_content,
        }
        resend.Emails.send(params)
        return True, f"A 6-digit verification code was sent to {user.email}."
    except Exception as e:
        logger.error(f"Resend error: {e}")
        print(f"\n[RESEND ERROR: {e}] Development OTP for {user.email}: {otp_code}\n")
        return False, f"Resend error: {str(e)}. (Development OTP: {otp_code})"
