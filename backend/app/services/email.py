import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("app.services.email")


class EmailService:
    """
    Enterprise Email Dispatching Service.
    Handles verification dispatches, password reset invitations, and alerts.
    Operates in a resilient, fall-back mode by writing structured developer logs
    when SMTP credentials are unconfigured, ensuring complete local testability.
    """

    def __init__(self) -> None:
        # Load standard mail configurations with sensible defaults
        self.smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", None)
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        self.sender_email = getattr(settings, "SENDER_EMAIL", "noreply@jobcatalyst.ai")

    def _send_email_smtp(self, recipient: str, subject: str, html_content: str) -> bool:
        """Helper to compile and dispatch email via configured SMTP server."""
        if not self.smtp_user or not self.smtp_password:
            # Fallback to local structured developer logs
            logger.warning(
                f"[EMAIL SERVICE OFF-LINE] Real SMTP is unconfigured. "
                f"Logging dispatch target details:\n"
                f"Recipient: {recipient}\n"
                f"Subject: {subject}\n"
                f"Message Content HTML preview:\n{html_content}\n"
                f"=================================================="
            )
            return True

        try:
            # Build multipart message standard
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient

            # Attach HTML part
            part = MIMEText(html_content, "html")
            message.attach(part)

            # Establish secure transport channel
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()  # Upgrade connection to secure TLS channel
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender_email, recipient, message.as_string())
                
            logger.info(f"Successfully dispatched SMTP email to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch email to {recipient} via SMTP: {str(e)}")
            return False

    def send_verification_email(self, email: str, token: str) -> bool:
        """
        Dispatches email verification activation link to registered users.
        """
        activation_link = f"https://jobcatalyst.ai/verify-email?token={token}"
        subject = "JobCatalyst AI - Verify Your Account Email"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2563eb;">Activate Your JobCatalyst AI Account</h2>
                <p>Welcome to JobCatalyst AI! To activate your account, please verify your email address by clicking the link below:</p>
                <div style="margin: 24px 0;">
                    <a href="{activation_link}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Verify Email Address</a>
                </div>
                <p>If the button doesn't work, copy and paste this URL into your browser:</p>
                <p style="word-break: break-all; color: #666;">{activation_link}</p>
                <p>This verification link will expire in 24 hours.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin-top: 24px;" />
                <p style="font-size: 11px; color: #999;">This is an automated security email. Please do not reply directly.</p>
            </body>
        </html>
        """
        return self._send_email_smtp(email, subject, html_content)

    def send_password_reset_email(self, email: str, token: str) -> bool:
        """
        Dispatches secure password recovery invitation.
        """
        reset_link = f"https://jobcatalyst.ai/reset-password?token={token}"
        subject = "JobCatalyst AI - Reset Your Account Password"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #dc2626;">Password Reset Request</h2>
                <p>We received a request to reset the password for your JobCatalyst AI account. Click the button below to establish new credentials:</p>
                <div style="margin: 24px 0;">
                    <a href="{reset_link}" style="background-color: #dc2626; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Reset My Password</a>
                </div>
                <p>If you did not request this change, please ignore this email; your account credentials will remain unchanged.</p>
                <p>If the button doesn't work, copy and paste this URL into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_link}</p>
                <p>This reset link will expire in 1 hour.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin-top: 24px;" />
                <p style="font-size: 11px; color: #999;">This is an automated security email. Please do not reply directly.</p>
            </body>
        </html>
        """
        return self._send_email_smtp(email, subject, html_content)
