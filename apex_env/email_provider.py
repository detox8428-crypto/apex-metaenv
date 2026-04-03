"""
Email Provider Integration for APEX
Supports: Gmail, Outlook, SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import os

class EmailProvider:
    """Base email provider"""
    
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        raise NotImplementedError

class GmailProvider(EmailProvider):
    """Gmail SMTP Provider"""
    
    def __init__(self, email: str, app_password: str):
        """
        Initialize Gmail provider
        
        Args:
            email: Gmail address
            app_password: Gmail app-specific password (not regular password)
                         Generate at: https://myaccount.google.com/apppasswords
        """
        self.email = email
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send email via Gmail"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email
            msg['To'] = recipient
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.app_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Gmail send error: {e}")
            return False

class OutlookProvider(EmailProvider):
    """Outlook/Hotmail SMTP Provider"""
    
    def __init__(self, email: str, password: str):
        """Initialize Outlook provider"""
        self.email = email
        self.password = password
        self.smtp_server = "smtp-mail.outlook.com"
        self.smtp_port = 587
    
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send email via Outlook"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email
            msg['To'] = recipient
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Outlook send error: {e}")
            return False

class SMTPProvider(EmailProvider):
    """Generic SMTP Provider"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        """Initialize custom SMTP provider"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
    
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email
            msg['To'] = recipient
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"SMTP send error: {e}")
            return False

class EmailManager:
    """Manages email sending across providers"""
    
    def __init__(self):
        self.provider: Optional[EmailProvider] = None
        self.enabled = False
        self.contacts = {}
    
    def setup_gmail(self, email: str, app_password: str):
        """Setup Gmail provider"""
        self.provider = GmailProvider(email, app_password)
        self.enabled = True
        print(f"Gmail provider initialized for {email}")
    
    def setup_outlook(self, email: str, password: str):
        """Setup Outlook provider"""
        self.provider = OutlookProvider(email, password)
        self.enabled = True
        print(f"Outlook provider initialized for {email}")
    
    def setup_smtp(self, smtp_server: str, smtp_port: int, email: str, password: str):
        """Setup custom SMTP provider"""
        self.provider = SMTPProvider(smtp_server, smtp_port, email, password)
        self.enabled = True
        print(f"SMTP provider initialized for {email}")
    
    def add_contact(self, contact_id: int, email: str, name: str = "Contact"):
        """Map contact ID to real email"""
        self.contacts[contact_id] = {
            'email': email,
            'name': name
        }
    
    def resolve_email(self, contact_id: int) -> Optional[str]:
        """Get real email from contact ID"""
        contact = self.contacts.get(contact_id)
        if contact:
            return contact['email']
        return None
    
    def send_email(self, recipient_id: int, subject: str, body: str) -> bool:
        """Send real email"""
        if not self.enabled or not self.provider:
            return False
        
        recipient_email = self.resolve_email(recipient_id)
        if not recipient_email:
            print(f"Contact ID {recipient_id} not found")
            return False
        
        return self.provider.send_email(recipient_email, subject, body)

# Global email manager
email_manager = EmailManager()

def load_email_config_from_env():
    """Load email configuration from environment variables"""
    provider = os.getenv('EMAIL_PROVIDER', '').lower()
    
    if provider == 'gmail':
        email = os.getenv('GMAIL_EMAIL')
        app_password = os.getenv('GMAIL_APP_PASSWORD')
        if email and app_password:
            email_manager.setup_gmail(email, app_password)
    
    elif provider == 'outlook':
        email = os.getenv('OUTLOOK_EMAIL')
        password = os.getenv('OUTLOOK_PASSWORD')
        if email and password:
            email_manager.setup_outlook(email, password)
    
    elif provider == 'smtp':
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email = os.getenv('SMTP_EMAIL')
        password = os.getenv('SMTP_PASSWORD')
        if all([smtp_server, email, password]):
            email_manager.setup_smtp(smtp_server, smtp_port, email, password)
