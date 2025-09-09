"""
Email service for sending verification emails, password reset emails, and invitations.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class EmailService:
    """Email service for sending various types of emails."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
    
    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """Send email using SMTP."""
        try:
            if not self.smtp_host or not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP not configured, email not sent", to_email=to_email, subject=subject)
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info("Email sent successfully", to_email=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("Error sending email", error=str(e), to_email=to_email, subject=subject)
            return False
    
    def send_verification_email(self, email: str, username: str, verification_url: str) -> bool:
        """Send email verification email."""
        subject = "Verify your email address"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; }}
                .content {{ padding: 20px; }}
                .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to AI Writer!</h1>
                </div>
                <div class="content">
                    <p>Hi {username},</p>
                    <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
                        {verification_url}
                    </p>
                    <p>This link will expire in 24 hours.</p>
                </div>
                <div class="footer">
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                    <p>&copy; 2024 AI Writer. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to AI Writer!
        
        Hi {username},
        
        Thank you for signing up! Please verify your email address by visiting this link:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, you can safely ignore this email.
        
        Best regards,
        The AI Writer Team
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_password_reset_email(self, email: str, username: str, reset_url: str) -> bool:
        """Send password reset email."""
        subject = "Reset your password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; }}
                .content {{ padding: 20px; }}
                .button {{ display: inline-block; background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hi {username},</p>
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
                        {reset_url}
                    </p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 AI Writer. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {username},
        
        We received a request to reset your password. Visit this link to reset it:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        Best regards,
        The AI Writer Team
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_organization_invitation_email(
        self, 
        email: str, 
        inviter_name: str, 
        organization_name: str, 
        role: str,
        invitation_url: str,
        message: Optional[str] = None
    ) -> bool:
        """Send organization invitation email."""
        subject = f"You're invited to join {organization_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Organization Invitation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; }}
                .content {{ padding: 20px; }}
                .button {{ display: inline-block; background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; font-size: 14px; color: #666; }}
                .message {{ background-color: #e9ecef; padding: 15px; border-radius: 4px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>You're Invited!</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p><strong>{inviter_name}</strong> has invited you to join <strong>{organization_name}</strong> as a <strong>{role}</strong>.</p>
                    {f'<div class="message"><p><strong>Message from {inviter_name}:</strong></p><p>{message}</p></div>' if message else ''}
                    <p>Click the button below to accept the invitation:</p>
                    <p style="text-align: center;">
                        <a href="{invitation_url}" class="button">Accept Invitation</a>
                    </p>
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
                        {invitation_url}
                    </p>
                    <p>This invitation will expire in 7 days.</p>
                </div>
                <div class="footer">
                    <p>If you don't want to join this organization, you can safely ignore this email.</p>
                    <p>&copy; 2024 AI Writer. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        You're Invited!
        
        Hi there,
        
        {inviter_name} has invited you to join {organization_name} as a {role}.
        
        {f'Message from {inviter_name}: {message}' if message else ''}
        
        Accept the invitation by visiting this link:
        
        {invitation_url}
        
        This invitation will expire in 7 days.
        
        If you don't want to join this organization, you can safely ignore this email.
        
        Best regards,
        The AI Writer Team
        """
        
        return self._send_email(email, subject, html_content, text_content)
    
    def send_welcome_email(self, email: str, username: str) -> bool:
        """Send welcome email after successful registration."""
        subject = "Welcome to AI Writer!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to AI Writer</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; }}
                .content {{ padding: 20px; }}
                .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to AI Writer!</h1>
                </div>
                <div class="content">
                    <p>Hi {username},</p>
                    <p>Welcome to AI Writer! Your account has been successfully created and verified.</p>
                    <p>You can now start creating amazing content with the power of AI. Here are some things you can do:</p>
                    <ul>
                        <li>Create and manage your writing styles</li>
                        <li>Generate articles with AI assistance</li>
                        <li>Collaborate with team members</li>
                        <li>Export your content in various formats</li>
                    </ul>
                    <p style="text-align: center;">
                        <a href="http://localhost:3000/dashboard" class="button">Go to Dashboard</a>
                    </p>
                    <p>If you have any questions, feel free to reach out to our support team.</p>
                </div>
                <div class="footer">
                    <p>Happy writing!</p>
                    <p>&copy; 2024 AI Writer. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to AI Writer!
        
        Hi {username},
        
        Welcome to AI Writer! Your account has been successfully created and verified.
        
        You can now start creating amazing content with the power of AI. Here are some things you can do:
        
        - Create and manage your writing styles
        - Generate articles with AI assistance
        - Collaborate with team members
        - Export your content in various formats
        
        Visit your dashboard: http://localhost:3000/dashboard
        
        If you have any questions, feel free to reach out to our support team.
        
        Happy writing!
        The AI Writer Team
        """
        
        return self._send_email(email, subject, html_content, text_content)
