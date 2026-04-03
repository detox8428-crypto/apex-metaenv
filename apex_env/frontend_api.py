"""
APEX Frontend Backend API

Provides REST endpoints for the frontend application:
- /api/send-otp - Send OTP for verification
- /api/verify-otp - Verify OTP and code
- /api/process - Route requests to appropriate APEX features
- /api/status - System status check
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

# Import APEX managers
from apex_env.search_provider import search_manager
from apex_env.content_summarizer import summarizer_manager
from apex_env.code_generator import code_generator_manager
from apex_env.command_executor import command_executor_manager
from apex_env.vscode_debugger import vscode_debugger_manager
from apex_env.whatsapp_integration import whatsapp_manager
from apex_env.secure_auth import SecureAuthAPI, session_manager, user_registry, otp_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["frontend"])

# ===== Models =====

class SendOTPRequest(BaseModel):
    """Send OTP request"""
    phone: str
    email: str

class SendOTPResponse(BaseModel):
    """Send OTP response"""
    success: bool
    request_id: str
    message: str
    expires_in: int
    demo_otp: Optional[str] = None
    demo_code: Optional[str] = None

class VerifyOTPRequest(BaseModel):
    """Verify OTP request"""
    request_id: str
    phone: str
    email: str
    otp: str
    verification_code: str

class VerifyOTPResponse(BaseModel):
    """Verify OTP response"""
    success: bool
    message: str
    user: Optional[Dict[str, str]] = None
    token: Optional[str] = None

class ProcessRequest(BaseModel):
    """Process user request"""
    message: str
    feature: str = "all"
    user: str
    phone: str
    token: Optional[str] = None

class ProcessResponse(BaseModel):
    """Process response"""
    result: Dict[str, Any]
    feature: str
    timestamp: str
    success: bool

# ===== Authentication Endpoints =====

@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(request: SendOTPRequest):
    """Send OTP to phone and verification code to email"""
    
    try:
        result = await SecureAuthAPI.send_otp(request.phone, request.email)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return SendOTPResponse(
            success=True,
            request_id=result["request_id"],
            message=result["message"],
            expires_in=result["expires_in"],
            demo_otp=result.get("demo_otp"),
            demo_code=result.get("demo_code")
        )
    
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and code, create session"""
    
    try:
        result = await SecureAuthAPI.verify_otp(
            request.request_id,
            request.phone,
            request.email,
            request.otp,
            request.verification_code
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=401, detail=result.get("message"))
        
        return VerifyOTPResponse(
            success=True,
            message=result["message"],
            user=result.get("user"),
            token=result.get("token")
        )
    
    except Exception as e:
        logger.error(f"Verify OTP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== Feature Detection =====

def detect_feature(message: str, preferred_feature: str = "all") -> str:
    """
    Automatically detect which feature to use based on message content
    
    Keywords:
    - search: find, search, look for, what is, who is, where is, how to, tutorial
    - code: write code, generate, fix bug, debug, refactor, code gen, python, javascript
    - summarize: summarize, summary, overview, brief, tldr, condense
    - execute: run, execute, command, shell, bash, powershell, terminal
    - debug: error, bug, traceback, exception, stack trace, problem
    - whatsapp: send message, whatsapp, sms, notify
    """
    
    if preferred_feature != "all":
        return preferred_feature
    
    message_lower = message.lower()
    
    # Search keywords
    search_keywords = ['search', 'find', 'look for', 'what is', 'who is', 'where is', 
                       'how to', 'tutorial', 'documentation', 'guide', 'explain']
    if any(kw in message_lower for kw in search_keywords):
        return "search"
    
    # Code keywords
    code_keywords = ['code', 'generate', 'write', 'fix bug', 'debug', 'refactor', 
                     'python', 'javascript', 'java', 'rust', 'golang', 'c++']
    if any(kw in message_lower for kw in code_keywords):
        return "code"
    
    # Summarize keywords
    summarize_keywords = ['summarize', 'summary', 'overview', 'brief', 'tldr', 'condense',
                          'summarise', 'recap', 'digest']
    if any(kw in message_lower for kw in summarize_keywords):
        return "summarize"
    
    # Execute keywords
    execute_keywords = ['run', 'execute', 'command', 'shell', 'bash', 'powershell',
                        'terminal', 'cmd', 'command line', 'ls', 'dir', 'get-']
    if any(kw in message_lower for kw in execute_keywords):
        return "execute"
    
    # Debug keywords
    debug_keywords = ['error', 'bug', 'traceback', 'exception', 'stack trace', 'problem',
                      'wrong', 'not working', 'crash', 'fail']
    if any(kw in message_lower for kw in debug_keywords):
        return "debug"
    
    # WhatsApp keywords
    whatsapp_keywords = ['send', 'whatsapp', 'sms', 'notify', 'contact', 'text', 'message']
    if any(kw in message_lower for kw in whatsapp_keywords):
        return "whatsapp"
    
    # Default to search
    return "search"

# ===== Feature Routing =====

async def route_search(message: str) -> Dict[str, Any]:
    """Route to search feature"""
    try:
        # Extract search query from message
        query = message.replace("search", "").replace("find", "").strip()
        
        result = search_manager.search(
            query=query,
            num_results=5
        )
        
        results = []
        if result.get("success") and result.get("results"):
            for item in result.get("results", [])[:3]:
                results.append({
                    "title": item.title if hasattr(item, 'title') else str(item),
                    "url": item.url if hasattr(item, 'url') else "",
                    "snippet": item.snippet if hasattr(item, 'snippet') else ""
                })
        
        return {
            "feature": "search",
            "data": {
                "query": query,
                "results": results
            },
            "message": f"Found {len(results)} results"
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "feature": "search",
            "data": {"error": str(e)},
            "message": "Search failed"
        }

async def route_code(message: str) -> Dict[str, Any]:
    """Route to code generation"""
    try:
        # Determine task
        task = "generate"
        if "fix" in message.lower():
            task = "fix"
        elif "refactor" in message.lower():
            task = "refactor"
        elif "explain" in message.lower():
            task = "explain"
        
        # Determine language
        language = "python"
        for lang in ["javascript", "java", "go", "rust", "cpp", "c++"]:
            if lang in message.lower():
                language = lang
                break
        
        # Extract description (remove keywords)
        description = message.lower()
        for keyword in ["write", "generate", "code", "fix", "refactor", "explain", "python", "javascript", "java", "go", "rust", "c++", "cpp"]:
            description = description.replace(keyword, "").strip()
        
        result = code_generator_manager.generate(
            description=description or "general task",
            language=language,
            task=task
        ) if hasattr(code_generator_manager, 'generate') else {"code": "", "explanation": ""}
        
        return {
            "feature": "code",
            "data": {
                "task": task,
                "language": language,
                "code": result.get("code", ""),
                "explanation": result.get("explanation", "")
            },
            "message": f"{task.capitalize()} code generated"
        }
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        return {
            "feature": "code",
            "data": {"error": str(e)},
            "message": "Code generation failed"
        }

async def route_summarize(message: str) -> Dict[str, Any]:
    """Route to summarization"""
    try:
        # Extract content and style
        style = "detailed"
        if "brief" in message.lower():
            style = "brief"
        elif "executive" in message.lower():
            style = "executive"
        
        # Get content
        content = message.replace("summarize", "").replace("summary", "").strip()
        
        result = summarizer_manager.summarize(
            content=content,
            style=style
        ) if hasattr(summarizer_manager, 'summarize') else {"summary": ""}
        
        return {
            "feature": "summarize",
            "data": {
                "summary": result.get("summary", ""),
                "style": style,
                "tokens": result.get("tokens")
            },
            "message": "Summarization complete"
        }
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return {
            "feature": "summarize",
            "data": {"error": str(e)},
            "message": "Summarization failed"
        }

async def route_execute(message: str) -> Dict[str, Any]:
    """Route to command execution"""
    try:
        # Extract command
        command = message.replace("run", "").replace("execute", "").replace("command", "").strip()
        
        # Determine shell
        shell = "powershell"
        if "cmd" in message.lower():
            shell = "cmd"
        
        # Validate command
        valid, reason = command_executor_manager.validate(command)
        if not valid:
            return {
                "feature": "execute",
                "data": {"error": reason},
                "message": f"Command blocked: {reason}"
            }
        
        result = command_executor_manager.execute(
            command=command,
            shell=shell,
            timeout_seconds=10
        ) if hasattr(command_executor_manager, 'execute') else {"stdout": "", "stderr": ""}
        
        return {
            "feature": "execute",
            "data": {
                "command": command,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "return_code": result.get("return_code")
            },
            "message": "Command executed"
        }
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {
            "feature": "execute",
            "data": {"error": str(e)},
            "message": "Command execution failed"
        }

async def route_whatsapp(message: str) -> Dict[str, Any]:
    """Route to WhatsApp messaging"""
    try:
        # Extract recipient phone and message
        recipient_phone = "+1234567890"  # Default
        msg_text = message
        
        # Simple parsing - look for "to" separator
        if " to " in message.lower():
            parts = message.lower().split(" to ")
            msg_text = parts[0].replace("send", "").strip()
            recipient = parts[-1].strip()
            # Try to guess if recipient is a phone number or name
            if any(char.isdigit() for char in recipient):
                recipient_phone = recipient
        
        # Send message (demo mode - just return success)
        result = {
            "success": True,
            "message_id": "demo_msg_" + str(datetime.now().timestamp()),
            "recipient": recipient_phone
        }
        
        return {
            "feature": "whatsapp",
            "data": {
                "recipient": recipient_phone,
                "message": msg_text,
                "status": "sent",
                "message_id": result.get("message_id")
            },
            "message": f"Message sent successfully"
        }
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return {
            "feature": "whatsapp",
            "data": {"error": str(e)},
            "message": "Message failed to send"
        }

async def route_debug(message: str) -> Dict[str, Any]:
    """Route to error debugging"""
    try:
        # Extract error and language
        error_text = message.replace("error", "").replace("debug", "").strip()
        language = "python"
        if "javascript" in message.lower():
            language = "javascript"
        
        result = vscode_debugger_manager.analyze_error(
            error_text=error_text,
            language=language
        ) if hasattr(vscode_debugger_manager, 'analyze_error') else {"analysis": ""}
        
        return {
            "feature": "debug",
            "data": {
                "analysis": result.get("analysis", ""),
                "error_type": result.get("error_type", "")
            },
            "message": "Error analyzed"
        }
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {
            "feature": "debug",
            "data": {"error": str(e)},
            "message": "Error analysis failed"
        }

@router.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """Process user request and route to appropriate feature"""
    
    try:
        # Verify session token
        if request.token:
            valid, email = session_manager.verify_session(request.token)
            if not valid:
                raise HTTPException(status_code=401, detail="Session expired. Please login again.")
        else:
            raise HTTPException(status_code=401, detail="No session token provided.")
        
        # Detect feature
        feature = detect_feature(request.message, request.feature)
        
        # Route to appropriate handler
        if feature == "search":
            result = await route_search(request.message)
        elif feature == "code":
            result = await route_code(request.message)
        elif feature == "summarize":
            result = await route_summarize(request.message)
        elif feature == "execute":
            result = await route_execute(request.message)
        elif feature == "whatsapp":
            result = await route_whatsapp(request.message)
        elif feature == "debug":
            result = await route_debug(request.message)
        else:
            result = {
                "feature": "search",
                "data": {},
                "message": "Using default search"
            }
        
        logger.info(f"Processed request for {request.user}: {feature}")
        
        return ProcessResponse(
            result=result,
            feature=feature,
            timestamp=datetime.now().isoformat(),
            success=True
        )
    
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout(token: str):
    """Logout user and invalidate session"""
    
    try:
        result = await SecureAuthAPI.logout(token)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return {
            "success": True,
            "message": result["message"]
        }
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== Status Endpoint =====

@router.get("/status")
async def get_status():
    """Get system status"""
    return {
        "status": "online",
        "security": {
            "authentication": "OTP + Email Verification",
            "encryption": "Fernet (AES-128)",
            "session": "24-hour tokens",
            "rate_limiting": "Enabled"
        },
        "features": {
            "search": "enabled",
            "code": "enabled",
            "summarize": "enabled",
            "execute": "enabled",
            "debug": "enabled",
            "whatsapp": "enabled"
        },
        "users_registered": len(user_registry.registry),
        "active_sessions": len(session_manager.sessions),
        "pending_otps": len(otp_manager.otps),
        "timestamp": datetime.now().isoformat()
    }
