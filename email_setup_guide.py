"""
Email Integration Setup Guide for APEX

This file demonstrates how to configure real email sending in your APEX environment.

QUICK START:
1. Copy .env.example to .env
2. Fill in your email provider credentials
3. Restart the API server
4. Set send_real=True when making email actions

SUPPORTED PROVIDERS:
- Gmail (requires app-specific password)
- Outlook/Hotmail (requires app-specific password)
- Custom SMTP (any provider: SendGrid, AWS SES, etc.)
"""

from apex_env.email_provider import email_manager, load_email_config_from_env
import os
from typing import List, Tuple

def initialize_email_provider() -> Tuple[bool, str]:
    """
    Initialize email provider from environment variables.
    
    Returns:
        (success: bool, message: str)
    
    Example usage in server startup:
        success, message = initialize_email_provider()
        if success:
            logger.info(f"✓ Email integration initialized: {message}")
        else:
            logger.warning(f"✓ Email simulation mode (no real emails): {message}")
    """
    try:
        config = load_email_config_from_env()
        
        if not config or config.get("enabled") is False:
            return True, "Email simulation mode active (no real emails will be sent)"
        
        provider_type = config.get("provider")
        
        if provider_type == "gmail":
            email_manager.setup_gmail(
                config.get("email"),
                config.get("app_password")
            )
            return True, f"Gmail provider initialized ({config.get('email')})"
            
        elif provider_type == "outlook":
            email_manager.setup_outlook(
                config.get("email"),
                config.get("password")
            )
            return True, f"Outlook provider initialized ({config.get('email')})"
            
        elif provider_type == "smtp":
            email_manager.setup_smtp(
                config.get("server"),
                config.get("port", 587),
                config.get("email"),
                config.get("password")
            )
            return True, f"SMTP provider initialized ({config.get('email')} via {config.get('server')})"
        
        return True, "Email simulation mode (provider not configured)"
        
    except Exception as e:
        return True, f"Email simulation mode (init error: {str(e)})"


def setup_default_contacts() -> List[str]:
    """
    Add default contact mappings from environment.
    
    This reads CONTACT_N_EMAIL and CONTACT_N_NAME variables.
    
    Returns:
        List of contact IDs that were added
    """
    added_contacts = []
    
    for i in range(1, 101):  # Support up to 100 predefined contacts
        email_var = f"CONTACT_{i}_EMAIL"
        name_var = f"CONTACT_{i}_NAME"
        
        email = os.getenv(email_var)
        name = os.getenv(name_var)
        
        if email:
            email_manager.add_contact(i, email, name or f"Contact {i}")
            added_contacts.append(str(i))
    
    return added_contacts


# EXAMPLE USAGE IN SERVER STARTUP:
# 
# @app.on_event("startup")
# async def startup_event():
#     # Initialize email provider
#     success, message = initialize_email_provider()
#     logger.info(f"Email Setup: {message}")
#     
#     # Setup contacts
#     contacts = setup_default_contacts()
#     if contacts:
#         logger.info(f"Added contacts: {', '.join(contacts)}")
#
#     # At this point, email_manager is ready to use
#     # API endpoints will automatically use real email if:
#     # 1. Credentials are configured in .env
#     # 2. send_real=True in the EmailAction


# EMAIL ACTION EXAMPLE:
# 
# POST /actions/execute
# {
#   "type": "email",
#   "recipient_id": 1,
#   "subject": "Hello from APEX",
#   "body": "This is a real email sent from APEX!",
#   "send_real": true,  # <-- Set this to True to send actual email
#   "language": "EN",
#   "priority": "HIGH"
# }


print("✓ Email integration setup module loaded")
print("✓ Use initialize_email_provider() to set up email sending")
print("✓ Use setup_default_contacts() to add contact mappings")
