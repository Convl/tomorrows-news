"""Email service for sending authentication emails."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.core.config import settings


def build_api_url(endpoint: str) -> str:
    """Build a complete Frontend URL to the correct static page with token preserved."""
    # endpoint examples: "verify?token=..." or "reset-password?token=..."
    if endpoint.startswith("verify?"):
        return f"{settings.FRONTEND_URL}/app/verify.html{endpoint[len('verify') :]}"
    if endpoint.startswith("reset-password?"):
        return f"{settings.FRONTEND_URL}/app/reset-password.html{endpoint[len('reset-password') :]}"
    # Fallback
    return f"{settings.FRONTEND_URL}/app/{endpoint}"


class EmailService:
    """Service for sending emails via SMTP."""

    @staticmethod
    async def send_email(
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: str = None,
    ) -> bool:
        """Send an email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.PROJECT_EMAIL_FROM_NAME} <{settings.PROJECT_EMAIL}>"
            msg["To"] = ", ".join(to_emails)

            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(settings.PROJECT_EMAIL_HOST, settings.PROJECT_EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.PROJECT_EMAIL, settings.PROJECT_EMAIL_PASSWORD.get_secret_value())
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    @staticmethod
    async def send_verification_email(email: str, token: str) -> bool:
        """Send verification email to user."""
        verification_url = build_api_url(f"verify?token={token}")

        html_content = f"""
        <html>
            <body>
                <h2>Verify Your Email Address</h2>
                <p>Thank you for registering with Tomorrow's News!</p>
                <p>Please click the link below to verify your email address:</p>
                <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p>{verification_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't create an account, please ignore this email.</p>
            </body>
        </html>
        """

        text_content = f"""
        Verify Your Email Address
        
        Thank you for registering with Tomorrow's News!
        
        Please visit the following link to verify your email address:
        {verification_url}
        
        This link will expire in 1 hour.
        
        If you didn't create an account, please ignore this email.
        """

        return await EmailService.send_email(
            to_emails=[email],
            subject="Verify Your Email Address - Tomorrow's News",
            html_content=html_content,
            text_content=text_content,
        )

    @staticmethod
    async def send_password_reset_email(email: str, token: str) -> bool:
        """Send password reset email to user."""
        reset_url = build_api_url(f"reset-password?token={token}")

        html_content = f"""
        <html>
            <body>
                <h2>Reset Your Password</h2>
                <p>We received a request to reset your password for your Tomorrow's News account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p>{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
            </body>
        </html>
        """

        text_content = f"""
        Reset Your Password
        
        We received a request to reset your password for your Tomorrow's News account.
        
        Please visit the following link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        """

        return await EmailService.send_email(
            to_emails=[email],
            subject="Reset Your Password - Tomorrow's News",
            html_content=html_content,
            text_content=text_content,
        )
