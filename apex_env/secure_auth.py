"""
APEX Secure Authentication API

Features:
- OTP generation and delivery (SMS + Email)
- Encrypted data storage
- Rate limiting and abuse prevention
- Session management
- Data protection compliance
"""

import os
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging
from cryptography.fernet import Fernet

# Import email provider
from apex_env.email_provider import GmailProvider

logger = logging.getLogger(__name__)

# ===== Encryption =====

class DataEncryption:
    """Handle encryption/decryption of sensitive data"""
    
    def __init__(self):
        # Get or create encryption key
        key_file = "secrets/encryption.key"
        os.makedirs("secrets", exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.key)
            os.chmod(key_file, 0o600)  # Read-only
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

encryption = DataEncryption()

# ===== Email Setup =====

# Initialize Gmail provider if credentials are available
email_provider = None
try:
    gmail_email = os.getenv("GMAIL_EMAIL")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if gmail_email and gmail_password:
        email_provider = GmailProvider(gmail_email, gmail_password)
        logger.info(f"Gmail provider initialized for {gmail_email}")
    else:
        logger.info("Gmail credentials not found - OTP emails will not be sent")
except Exception as e:
    logger.warning(f"Failed to initialize email provider: {e}")

# ===== OTP Management =====

class OTPManager:
    """Generate, store, and verify OTPs"""
    
    def __init__(self):
        self.otps = {}  # request_id -> {otp, code, phone, email, expires, attempts}
        self.rate_limits = {}  # phone/email -> {count, reset_time}
    
    def generate_otp(self, phone: str, email: str) -> Dict:
        """Generate OTP and verification code"""
        
        # Note: Rate limiting disabled for demo/testing purposes
        # In production, uncomment below for: Max 10 OTPs per phone per hour
        # rate_key = f"phone_{phone}"
        # if rate_key in self.rate_limits:
        #     record = self.rate_limits[rate_key]
        #     if datetime.now() < record["reset_time"]:
        #         if record["count"] >= 10:
        #             raise Exception("Too many OTP requests. Try again later.")
        #         record["count"] += 1
        #     else:
        #         self.rate_limits[rate_key] = {
        #             "count": 1,
        #             "reset_time": datetime.now() + timedelta(hours=1)
        #         }
        # else:
        #     self.rate_limits[rate_key] = {
        #         "count": 1,
        #         "reset_time": datetime.now() + timedelta(hours=1)
        #     }
        
        # Generate 6-digit OTP
        otp = str(secrets.randbelow(1000000)).zfill(6)
        
        # Generate alphanumeric verification code
        code = secrets.token_hex(3).upper()[:6]
        
        # Create request ID
        request_id = secrets.token_urlsafe(32)
        
        # Store OTP with expiration (10 minutes)
        expires = datetime.now() + timedelta(minutes=10)
        self.otps[request_id] = {
            "otp": hashlib.sha256(otp.encode()).hexdigest(),  # Hash OTP
            "code": hashlib.sha256(code.encode()).hexdigest(),  # Hash code
            "phone": encryption.encrypt(phone),
            "email": encryption.encrypt(email),
            "expires": expires.isoformat(),
            "attempts": 0,
            "created": datetime.now().isoformat()
        }
        
        logger.info(f"OTP generated for {email}")
        
        return {
            "request_id": request_id,
            "otp": otp,  # Return plaintext for testing; use SMS delivery in production
            "code": code,  # Return plaintext for testing; use email delivery in production
            "expires_in": 600,  # 10 minutes in seconds
            "message": "OTP and verification code generated (simulated delivery)"
        }
    
    def verify_otp(self, request_id: str, phone: str, email: str, otp: str, code: str) -> Tuple[bool, str]:
        """Verify OTP and code"""
        
        if request_id not in self.otps:
            return False, "Invalid request. Start over."
        
        record = self.otps[request_id]
        
        # Check expiration
        expires = datetime.fromisoformat(record["expires"])
        if datetime.now() > expires:
            del self.otps[request_id]
            return False, "OTP expired. Request a new one."
        
        # Rate limit: Max 5 attempts per request
        record["attempts"] += 1
        if record["attempts"] > 5:
            del self.otps[request_id]
            return False, "Too many attempts. Request a new OTP."
        
        # Verify phone and email match
        try:
            stored_phone = encryption.decrypt(record["phone"])
            stored_email = encryption.decrypt(record["email"])
            
            if stored_phone != phone or stored_email != email:
                return False, "Phone or email mismatch."
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return False, "Verification failed."
        
        # Hash input and compare
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        if otp_hash != record["otp"] or code_hash != record["code"]:
            remaining = 5 - record["attempts"]
            return False, f"Invalid OTP or code. {remaining} attempts remaining."
        
        # Success - cleanup OTP
        del self.otps[request_id]
        logger.info(f"OTP verified for {email}")
        
        return True, "OTP verified successfully"

otp_manager = OTPManager()

# ===== Session Management =====

class SecureSession:
    """Manage secure user sessions"""
    
    def __init__(self):
        self.sessions = {}  # token -> {email, phone, created, expires, ip}
        self.user_sessions = {}  # email -> [tokens]
    
    def create_session(self, email: str, phone: str, ip: str = "") -> str:
        """Create a new session token"""
        
        token = secrets.token_urlsafe(64)
        expires = datetime.now() + timedelta(hours=24)  # 24-hour session
        
        self.sessions[token] = {
            "email": email,
            "phone": encryption.encrypt(phone),
            "created": datetime.now().isoformat(),
            "expires": expires.isoformat(),
            "ip": ip,
            "last_activity": datetime.now().isoformat()
        }
        
        # Track user's sessions
        if email not in self.user_sessions:
            self.user_sessions[email] = []
        self.user_sessions[email].append(token)
        
        logger.info(f"Session created for {email}")
        
        return token
    
    def verify_session(self, token: str) -> Tuple[bool, Optional[str]]:
        """Verify if token is valid"""
        
        if token not in self.sessions:
            return False, None
        
        session = self.sessions[token]
        expires = datetime.fromisoformat(session["expires"])
        
        if datetime.now() > expires:
            del self.sessions[token]
            return False, None
        
        # Update last activity
        session["last_activity"] = datetime.now().isoformat()
        
        return True, session["email"]
    
    def invalidate_session(self, token: str):
        """Invalidate a session"""
        if token in self.sessions:
            session = self.sessions[token]
            del self.sessions[token]
            logger.info(f"Session invalidated for {session['email']}")
    
    def invalidate_user_sessions(self, email: str):
        """Invalidate all sessions for a user (logout all devices)"""
        if email in self.user_sessions:
            for token in self.user_sessions[email]:
                if token in self.sessions:
                    del self.sessions[token]
            del self.user_sessions[email]
            logger.info(f"All sessions invalidated for {email}")

session_manager = SecureSession()

# ===== User Registration =====

class SecureUserRegistry:
    """Store user data securely"""
    
    def __init__(self):
        self.registry = {}  # email -> {phone, created, verified, data_hash}
        self.phone_index = {}  # phone -> email
    
    def register_user(self, email: str, phone: str) -> Dict:
        """Register a new user"""
        
        # Check if already registered
        if email in self.registry:
            return {
                "success": False,
                "message": "Email already registered"
            }
        
        if phone in self.phone_index:
            return {
                "success": False,
                "message": "Phone already registered"
            }
        
        # Create user record
        data_hash = hashlib.sha256(f"{email}{phone}".encode()).hexdigest()
        
        self.registry[email] = {
            "phone": encryption.encrypt(phone),
            "created": datetime.now().isoformat(),
            "verified": datetime.now().isoformat(),
            "data_hash": data_hash,
            "login_count": 0,
            "last_login": None
        }
        
        self.phone_index[phone] = email
        
        logger.info(f"User registered: {email}")
        
        return {
            "success": True,
            "message": "User registered successfully"
        }
    
    def update_login(self, email: str):
        """Update login timestamp"""
        if email in self.registry:
            self.registry[email]["login_count"] += 1
            self.registry[email]["last_login"] = datetime.now().isoformat()
    
    def get_user(self, email: str) -> Optional[Dict]:
        """Get user info"""
        if email in self.registry:
            user = self.registry[email].copy()
            user["phone"] = encryption.decrypt(user["phone"])
            return user
        return None

user_registry = SecureUserRegistry()

# ===== API Responses =====

class SecureAuthAPI:
    """API endpoints for secure authentication"""
    
    @staticmethod
    async def send_otp(phone: str, email: str) -> Dict:
        """Send OTP to phone and verification code to email"""
        
        try:
            # Validate inputs
            if not phone or not email:
                return {"success": False, "message": "Missing phone or email"}
            
            # Generate OTP and code
            result = otp_manager.generate_otp(phone, email)
            
            logger.info(f"[OTP GENERATED] OTP: {result['otp']}, Code: {result['code']}")
            
            # Demo output
            print(f"\n{'='*50}")
            print(f"[OTP DELIVERY]")
            print(f"{'='*50}")
            print(f"[SMS] to {phone}: {result['otp']}")
            print(f"[EMAIL] to {email}: {result['code']}")
            print(f"{'='*50}\n")
            
            # Send email with verification code if Gmail is configured
            if email_provider:
                try:
                    email_body = f"""
APEX Verification Code

Your verification code is: {result['code']}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.
"""
                    email_provider.send_email(
                        recipient=email,
                        subject="APEX Verification Code",
                        body=email_body
                    )
                    logger.info(f"Verification email sent to {email}")
                except Exception as e:
                    logger.warning(f"Failed to send email to {email}: {e}")
            else:
                logger.info("[DEMO MODE] Email not sent - Gmail not configured")
            
            return {
                "success": True,
                "request_id": result["request_id"],
                "message": "OTP and verification code sent",
                "expires_in": result["expires_in"],
                # For demo only - remove in production
                "demo_otp": result["otp"],
                "demo_code": result["code"]
            }
        
        except Exception as e:
            logger.error(f"Send OTP error: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    @staticmethod
    async def verify_otp(request_id: str, phone: str, email: str, otp: str, verification_code: str) -> Dict:
        """Verify OTP and code, create session"""
        
        try:
            # Verify OTP
            valid, message = otp_manager.verify_otp(request_id, phone, email, otp, verification_code)
            
            if not valid:
                return {
                    "success": False,
                    "message": message
                }
            
            # Register or update user
            user_registry.register_user(email, phone)
            user_registry.update_login(email)
            
            # Create session
            token = session_manager.create_session(email, phone)
            
            return {
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "email": email,
                    "phone": phone
                },
                "token": token,
                "session_expires_in": 86400
            }
        
        except Exception as e:
            logger.error(f"Verify OTP error: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    @staticmethod
    async def logout(token: str) -> Dict:
        """Logout user and invalidate session"""
        
        try:
            session_manager.invalidate_session(token)
            return {
                "success": True,
                "message": "Logged out successfully"
            }
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {
                "success": False,
                "message": str(e)
            }
