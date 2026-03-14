"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Email service for sending verification and password reset emails.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from backend.shared.logging.logger import get_logger

logger = get_logger("auth-service.email")


class EmailService:
    """Send emails for authentication flows."""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: str = "KOROBOS",
    ):
        """
        Initialize email service.

        Args:
            smtp_server: SMTP server address (default: from env)
            smtp_port: SMTP port (default: from env)
            smtp_username: SMTP username (default: from env)
            smtp_password: SMTP password (default: from env)
            from_email: Email address to send from (default: from env or smtp_username)
            from_name: Display name for sender
        """
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or self.smtp_username or "noreply@korobos.app"
        self.from_name = from_name

        self.enabled = bool(self.smtp_username and self.smtp_password)

        if not self.enabled:
            logger.warning("Email service disabled: SMTP credentials not configured")

    async def send_verification_email(
        self,
        email: str,
        verification_token: str,
        username: str = "User",
        verification_url_base: str = "https://app.korobos.com",
    ) -> bool:
        """
        Send email verification email.

        Args:
            email: Recipient email address
            verification_token: Email verification token
            username: User's name for personalization
            verification_url_base: Base URL for verification link

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(
                f"Email service disabled, "
                f"skipping verification email to {email}"
            )
            return True  # Silently succeed in development

        verification_url = (
            f"{verification_url_base}/verify-email?token={verification_token}"
        )

        subject = "Verify your KOROBOS email"
        html_body = f"""
        <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;
                        color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Welcome to KOROBOS!</h2>
                    <p>Hi {username},</p>
                    <p>Thank you for signing up. Please verify your email
                       address to get started.</p>

                    <p style="margin: 30px 0;">
                        <a href="{verification_url}"
                           style="display: inline-block; padding: 12px 30px;
                                  background-color: #007bff; color: white;
                                  text-decoration: none; border-radius: 5px;
                                  font-weight: bold;">
                            Verify Email
                        </a>
                    </p>

                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #666;">
                        {verification_url}
                    </p>

                    <p style="margin-top: 40px; font-size: 12px; color: #999;">
                        This link expires in 24 hours. If you didn't create
                        this account, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """

        return await self._send_email(email, subject, html_body)

    async def send_password_reset_email(
        self,
        email: str,
        reset_token: str,
        username: str = "User",
        reset_url_base: str = "https://app.korobos.com",
    ) -> bool:
        """
        Send password reset email.

        Args:
            email: Recipient email address
            reset_token: Password reset token
            username: User's name for personalization
            reset_url_base: Base URL for reset link

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(
                f"Email service disabled, "
                f"skipping password reset email to {email}"
            )
            return True  # Silently succeed in development

        reset_url = f"{reset_url_base}/reset-password?token={reset_token}"

        subject = "Reset your KOROBOS password"
        html_body = f"""
        <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;
                        color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Password Reset Request</h2>
                    <p>Hi {username},</p>
                    <p>We received a request to reset your KOROBOS password.
                       Click the button below to set a new password.</p>

                    <p style="margin: 30px 0;">
                        <a href="{reset_url}"
                           style="display: inline-block; padding: 12px 30px;
                                  background-color: #28a745; color: white;
                                  text-decoration: none; border-radius: 5px;
                                  font-weight: bold;">
                            Reset Password
                        </a>
                    </p>

                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #666;">
                        {reset_url}
                    </p>

                    <p style="margin-top: 40px; color: #d9534f;">
                        <strong>Important:</strong> This link expires in 1
                        hour and can only be used once.
                    </p>

                    <p style="margin-top: 20px; font-size: 12px; color: #999;">
                        If you didn't request a password reset, you can
                        safely ignore this email.
                        Your account is secure.
                    </p>
                </div>
            </body>
        </html>
        """

        return await self._send_email(email, subject, html_body)

    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Use TLS encryption
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, [to_email], message.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as exc:
            logger.error(f"Failed to send email to {to_email}: {exc}")
            return False


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


async def send_verification_email(
    email: str,
    verification_token: str,
    username: str = "User",
    verification_url_base: str = "https://app.korobos.com",
) -> bool:
    """
    Send email verification email (helper function).

    Args:
        email: Recipient email
        verification_token: Email verification token
        username: User's name
        verification_url_base: Base URL for verification link

    Returns:
        True if sent successfully
    """
    service = get_email_service()
    return await service.send_verification_email(
        email, verification_token, username, verification_url_base
    )


async def send_password_reset_email(
    email: str,
    reset_token: str,
    username: str = "User",
    reset_url_base: str = "https://app.korobos.com",
) -> bool:
    """
    Send password reset email (helper function).

    Args:
        email: Recipient email
        reset_token: Password reset token
        username: User's name
        reset_url_base: Base URL for reset link

    Returns:
        True if sent successfully
    """
    service = get_email_service()
    return await service.send_password_reset_email(
        email, reset_token, username, reset_url_base
    )
