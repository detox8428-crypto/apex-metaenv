"""
WhatsApp Business API Integration Module
==========================================
Sends messages via WhatsApp Business API (Meta official)
Supports text messages, media, templates

Features:
- Text message sending
- Media sharing (images, documents)
- Template messages
- Contact management
- Message delivery tracking
- Error handling & validation
"""

import os
import json
import requests
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppContact:
    """WhatsApp contact with phone number and name"""
    phone: str  # E.164 format: +1234567890
    name: str
    contact_id: Optional[str] = None

    def validate(self) -> Tuple[bool, str]:
        """Validate phone number format"""
        if not self.phone.startswith("+"):
            return False, "Phone must start with +"
        if len(self.phone) < 10:
            return False, "Phone number too short"
        if not self.phone[1:].isdigit():
            return False, "Invalid phone number format"
        return True, ""


class WhatsAppProvider:
    """Base WhatsApp provider (abstract interface)"""
    
    def __init__(self):
        self.enabled = False
        self.provider_type = "whatsapp"
    
    def send_text(self, phone: str, message: str) -> Dict:
        """Send text message"""
        raise NotImplementedError
    
    def send_media(self, phone: str, media_url: str, caption: str = "") -> Dict:
        """Send media (image/document)"""
        raise NotImplementedError
    
    def send_template(self, phone: str, template_name: str, params: List[str]) -> Dict:
        """Send template message"""
        raise NotImplementedError
    
    def add_contact(self, contact: WhatsAppContact) -> Dict:
        """Add contact"""
        raise NotImplementedError


class WhatsAppBusinessAPI(WhatsAppProvider):
    """
    WhatsApp Business API provider using Meta's official API
    
    Requires:
    - WHATSAPP_PHONE_NUMBER_ID: Your WhatsApp Business Account phone number ID
    - WHATSAPP_ACCESS_TOKEN: Business Account access token
    - WHATSAPP_BUSINESS_ACCOUNT_ID: Business Account ID (optional)
    
    Setup Steps:
    1. Create Meta Business Account: https://business.facebook.com
    2. Set up WhatsApp Business API: https://developers.facebook.com/docs/whatsapp
    3. Get phone_number_id and access_token from settings
    4. Add to .env file
    """
    
    API_VERSION = "v18.0"
    BASE_URL = "https://graph.instagram.com"
    
    def __init__(self):
        super().__init__()
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
        self.contacts: Dict[str, WhatsAppContact] = {}
        
        # Validate credentials
        if self.phone_number_id and self.access_token:
            self.enabled = True
            logger.info("✅ WhatsApp Business API enabled")
        else:
            logger.warning("⚠️ WhatsApp Business API disabled - missing credentials")
    
    def _get_headers(self) -> Dict:
        """Get API request headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _api_call(self, endpoint: str, method: str = "POST", data: Dict = None) -> Dict:
        """Make API call to WhatsApp Business API"""
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{endpoint}"
            headers = self._get_headers()
            
            if method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            result = response.json()
            
            if response.status_code >= 400:
                logger.error(f"❌ WhatsApp API error: {result}")
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Unknown error"),
                    "code": response.status_code
                }
            
            return {"success": True, "data": result}
        
        except requests.RequestException as e:
            logger.error(f"❌ WhatsApp request failed: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {"success": False, "error": str(e)}
    
    def send_text(self, phone: str, message: str) -> Dict:
        """
        Send text message via WhatsApp
        
        Args:
            phone: Recipient phone in E.164 format (+1234567890)
            message: Message text
        
        Returns:
            {"success": bool, "message_id": str, "timestamp": str, ...}
        """
        
        # Validate phone
        contact = WhatsAppContact(phone, "Unknown")
        valid, error = contact.validate()
        if not valid:
            return {"success": False, "error": error}
        
        if not self.enabled:
            return {"success": False, "error": "WhatsApp API not configured"}
        
        # Prepare payload
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {"body": message}
        }
        
        # Send via API
        result = self._api_call(
            f"{self.phone_number_id}/messages",
            method="POST",
            data=payload
        )
        
        if result["success"]:
            message_id = result["data"].get("messages", [{}])[0].get("id", "unknown")
            return {
                "success": True,
                "message_id": message_id,
                "recipient": phone,
                "type": "text",
                "timestamp": datetime.now().isoformat(),
                "provider": "whatsapp_business_api"
            }
        else:
            return result
    
    def send_media(self, phone: str, media_url: str, media_type: str = "image",
                   caption: str = "") -> Dict:
        """
        Send media (image/document/video/audio)
        
        Args:
            phone: Recipient phone
            media_url: URL or local path to media
            media_type: "image", "document", "video", or "audio"
            caption: Optional caption (images only)
        
        Returns:
            Delivery status
        """
        
        # Validate
        contact = WhatsAppContact(phone, "Unknown")
        valid, error = contact.validate()
        if not valid:
            return {"success": False, "error": error}
        
        if not self.enabled:
            return {"success": False, "error": "WhatsApp API not configured"}
        
        if media_type not in ["image", "document", "video", "audio"]:
            return {"success": False, "error": f"Unsupported media type: {media_type}"}
        
        # Prepare payload
        media_object = {"link": media_url}
        if caption and media_type == "image":
            media_object["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": media_type,
            media_type: media_object
        }
        
        # Send
        result = self._api_call(
            f"{self.phone_number_id}/messages",
            method="POST",
            data=payload
        )
        
        if result["success"]:
            return {
                "success": True,
                "message_id": result["data"].get("messages", [{}])[0].get("id", "unknown"),
                "recipient": phone,
                "type": media_type,
                "timestamp": datetime.now().isoformat(),
                "provider": "whatsapp_business_api"
            }
        else:
            return result
    
    def send_template(self, phone: str, template_name: str,
                     params: Optional[List[str]] = None) -> Dict:
        """
        Send predefined template message
        
        Args:
            phone: Recipient phone
            template_name: Name of template (e.g., "hello_world")
            params: Template parameters
        
        Returns:
            Delivery status
        """
        
        contact = WhatsAppContact(phone, "Unknown")
        valid, error = contact.validate()
        if not valid:
            return {"success": False, "error": error}
        
        if not self.enabled:
            return {"success": False, "error": "WhatsApp API not configured"}
        
        # Prepare payload
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"}
            }
        }
        
        # Add parameters if provided
        if params:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in params]
                }
            ]
        
        # Send
        result = self._api_call(
            f"{self.phone_number_id}/messages",
            method="POST",
            data=payload
        )
        
        if result["success"]:
            return {
                "success": True,
                "message_id": result["data"].get("messages", [{}])[0].get("id", "unknown"),
                "recipient": phone,
                "template": template_name,
                "timestamp": datetime.now().isoformat(),
                "provider": "whatsapp_business_api"
            }
        else:
            return result
    
    def add_contact(self, contact: WhatsAppContact) -> Dict:
        """
        Add contact to local registry
        
        Args:
            contact: WhatsAppContact object
        
        Returns:
            {"success": bool, "contact_id": str}
        """
        
        valid, error = contact.validate()
        if not valid:
            return {"success": False, "error": error}
        
        # Store locally
        contact_id = f"wa_{len(self.contacts) + 1}"
        contact.contact_id = contact_id
        self.contacts[contact_id] = contact
        
        return {
            "success": True,
            "contact_id": contact_id,
            "name": contact.name,
            "phone": contact.phone
        }
    
    def get_contact(self, contact_id: str) -> Optional[WhatsAppContact]:
        """Get contact by ID"""
        return self.contacts.get(contact_id)
    
    def list_contacts(self) -> List[Dict]:
        """List all contacts"""
        return [
            {
                "contact_id": c.contact_id,
                "name": c.name,
                "phone": c.phone
            }
            for c in self.contacts.values()
        ]
    
    def get_status(self) -> Dict:
        """Get provider status"""
        return {
            "provider": "whatsapp_business_api",
            "enabled": self.enabled,
            "phone_number_id": self.phone_number_id if self.enabled else "not_configured",
            "contacts_registered": len(self.contacts),
            "status": "✅ Ready" if self.enabled else "⚠️ Not configured"
        }


class WhatsAppManager:
    """
    WhatsApp message manager - orchestrates sending via configured providers
    """
    
    def __init__(self):
        self.provider = WhatsAppBusinessAPI()
        self.enabled = self.provider.enabled
        logger.info(f"WhatsApp Manager initialized - {self.provider.get_status()['status']}")
    
    def send_message(self, phone: str, message: str) -> Dict:
        """Send text message"""
        return self.provider.send_text(phone, message)
    
    def send_media(self, phone: str, media_url: str, media_type: str = "image",
                   caption: str = "") -> Dict:
        """Send media message"""
        return self.provider.send_media(phone, media_url, media_type, caption)
    
    def send_template(self, phone: str, template_name: str,
                     params: Optional[List[str]] = None) -> Dict:
        """Send template message"""
        return self.provider.send_template(phone, template_name, params)
    
    def add_contact(self, phone: str, name: str) -> Dict:
        """Register contact"""
        contact = WhatsAppContact(phone, name)
        return self.provider.add_contact(contact)
    
    def get_status(self) -> Dict:
        """Get manager status"""
        return self.provider.get_status()


# Global manager instance
whatsapp_manager = WhatsAppManager()


if __name__ == "__main__":
    # Demo usage
    print("WhatsApp Integration Module")
    print("=" * 50)
    print(whatsapp_manager.get_status())
    print("\nTo use WhatsApp:")
    print("1. Create Meta Business Account")
    print("2. Configure WhatsApp Business API")
    print("3. Set environment variables:")
    print("   - WHATSAPP_PHONE_NUMBER_ID")
    print("   - WHATSAPP_ACCESS_TOKEN")
    print("   - WHATSAPP_BUSINESS_ACCOUNT_ID (optional)")
    print("4. Use whatsapp_manager.send_message(phone, text)")
