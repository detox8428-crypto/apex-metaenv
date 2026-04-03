"""
VS Code Debugger & Code Correction Module
===========================================
Helps debug code, analyze errors, and provide corrections within VS Code

Features:
- Stack trace analysis
- Error diagnosis
- Breakpoint management
- Variable inspection
- Code correction suggestions
- Debug logging
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAIN_AVAILABLE = False


class ErrorType(Enum):
    """Error classification"""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    TYPE = "type"
    NULL_REFERENCE = "null_reference"
    INDEX_OUT_OF_BOUNDS = "index_out_of_bounds"
    KEY_ERROR = "key_error"
    IMPORT_ERROR = "import_error"
    PERMISSION_ERROR = "permission_error"
    IO_ERROR = "io_error"
    UNKNOWN = "unknown"


class StackTraceParser:
    """Parse and analyze stack traces"""
    
    @staticmethod
    def parse_python_traceback(traceback: str) -> Dict:
        """Parse Python traceback"""
        
        lines = traceback.strip().split("\n")
        stack_frames = []
        error_message = ""
        error_type = ErrorType.UNKNOWN
        
        for idx, line in enumerate(lines):
            # Extract file and line number
            file_match = re.search(r'File "([^"]+)", line (\d+)', line)
            if file_match:
                stack_frames.append({
                    "file": file_match.group(1),
                    "line": int(file_match.group(2)),
                    "context": lines[idx+1] if idx+1 < len(lines) else ""
                })
            
            # Extract error message
            error_pattern = re.search(r"(\w+Error|Exception): (.+)", line)
            if error_pattern:
                error_type_str = error_pattern.group(1)
                error_message = error_pattern.group(2)
                
                # Classify error
                if "Syntax" in error_type_str:
                    error_type = ErrorType.SYNTAX
                elif "Type" in error_type_str:
                    error_type = ErrorType.TYPE
                elif "NameError" in error_type_str or "ReferenceError" in error_type_str:
                    error_type = ErrorType.NULL_REFERENCE
                elif "IndexError" in error_type_str:
                    error_type = ErrorType.INDEX_OUT_OF_BOUNDS
                elif "KeyError" in error_type_str:
                    error_type = ErrorType.KEY_ERROR
                elif "ImportError" in error_type_str or "ModuleNotFoundError" in error_type_str:
                    error_type = ErrorType.IMPORT_ERROR
                elif "PermissionError" in error_type_str:
                    error_type = ErrorType.PERMISSION_ERROR
                elif "IOError" in error_type_str or "FileNotFoundError" in error_type_str:
                    error_type = ErrorType.IO_ERROR
                else:
                    error_type = ErrorType.RUNTIME
        
        return {
            "language": "python",
            "error_type": error_type.value,
            "error_message": error_message,
            "stack_frames": stack_frames,
            "frame_count": len(stack_frames),
            "raw_traceback": traceback
        }
    
    @staticmethod
    def parse_javascript_error(error_str: str) -> Dict:
        """Parse JavaScript error"""
        
        stack_frames = []
        error_message = ""
        error_type = ErrorType.UNKNOWN
        
        lines = error_str.strip().split("\n")
        
        # First line is usually the error message
        if lines:
            first_line = lines[0]
            error_match = re.search(r"(\w+Error): (.+)", first_line)
            if error_match:
                error_type_str = error_match.group(1)
                error_message = error_match.group(2)
                
                if "Syntax" in error_type_str:
                    error_type = ErrorType.SYNTAX
                elif "Type" in error_type_str:
                    error_type = ErrorType.TYPE
                elif "Reference" in error_type_str:
                    error_type = ErrorType.NULL_REFERENCE
                else:
                    error_type = ErrorType.RUNTIME
        
        # Parse stack frames
        for line in lines[1:]:
            at_match = re.search(r"at\s+(.+)\s+\((.+):(\d+):(\d+)\)", line)
            if at_match:
                stack_frames.append({
                    "function": at_match.group(1),
                    "file": at_match.group(2),
                    "line": int(at_match.group(3)),
                    "column": int(at_match.group(4))
                })
        
        return {
            "language": "javascript",
            "error_type": error_type.value,
            "error_message": error_message,
            "stack_frames": stack_frames,
            "frame_count": len(stack_frames),
            "raw_traceback": error_str
        }
    
    @staticmethod
    def diagnose(parsed_trace: Dict) -> Dict:
        """Diagnose common error patterns"""
        
        diagnosis = {
            "likely_cause": "",
            "suggestions": [],
            "common_fix": ""
        }
        
        error_type = parsed_trace.get("error_type", "unknown")
        error_msg = parsed_trace.get("error_message", "").lower()
        
        # Diagnose based on error type
        if error_type == "syntax":
            diagnosis["likely_cause"] = "Code contains syntax error"
            diagnosis["suggestions"].append("Check for missing colons, brackets, or quotes")
            diagnosis["suggestions"].append("Verify indentation is correct")
            diagnosis["common_fix"] = "Fix grammar in code"
        
        elif error_type == "type":
            diagnosis["likely_cause"] = "Type mismatch or invalid type operation"
            diagnosis["suggestions"].append("Check variable types")
            diagnosis["suggestions"].append("Ensure operations are valid for types")
            diagnosis["common_fix"] = "Add type conversion or fix operation"
        
        elif error_type == "null_reference":
            diagnosis["likely_cause"] = "Accessing undefined/null variable"
            diagnosis["suggestions"].append("Check if variable is initialized")
            diagnosis["suggestions"].append("Add null checks before access")
            diagnosis["common_fix"] = "Initialize variable or add null check"
        
        elif error_type == "index_out_of_bounds":
            diagnosis["likely_cause"] = "Array index out of range"
            diagnosis["suggestions"].append("Check array length before accessing")
            diagnosis["suggestions"].append("Verify loop bounds")
            diagnosis["common_fix"] = "Add bounds checking"
        
        elif error_type == "key_error":
            diagnosis["likely_cause"] = "Dictionary key doesn't exist"
            diagnosis["suggestions"].append("Check if key exists before access")
            diagnosis["suggestions"].append("Use .get() with default value")
            diagnosis["common_fix"] = "Use .get() method or add key check"
        
        elif error_type == "import_error":
            diagnosis["likely_cause"] = "Module not found or not installed"
            diagnosis["suggestions"].append("Verify module name is correct")
            diagnosis["suggestions"].append("Install missing package")
            diagnosis["common_fix"] = "Install package or fix import name"
        
        else:
            diagnosis["likely_cause"] = "Runtime error occurred"
            diagnosis["suggestions"].append("Check the stack trace for error location")
            diagnosis["suggestions"].append("Review recent changes to code")
        
        return diagnosis


class VSCodeDebugger:
    """VS Code debugging and correction"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.enabled = OPENAI_AVAILABLE and self.api_key
        self.parser = StackTraceParser()
        self.breakpoints: List[Dict] = []
        self.watches: List[str] = []
        
        if self.enabled:
            import openai
            openai.api_key = self.api_key
            logger.info("✅ VS Code Debugger enabled")
        else:
            logger.warning("⚠️ VS Code Debugger disabled")
    
    def analyze_error(self, error_text: str, language: str = "python") -> Dict:
        """
        Analyze error and provide diagnosis
        
        Args:
            error_text: Stack trace or error message
            language: Programming language ("python", "javascript", etc.)
        
        Returns:
            {"error_analysis": {...}, "diagnosis": {...}, "fix_suggestions": [...]}
        """
        
        try:
            # Parse based on language
            if language.lower() == "python":
                parsed = self.parser.parse_python_traceback(error_text)
            elif language.lower() in ["javascript", "js", "typescript", "ts"]:
                parsed = self.parser.parse_javascript_error(error_text)
            else:
                parsed = self.parser.parse_python_traceback(error_text)
            
            # Diagnose
            diagnosis = self.parser.diagnose(parsed)
            
            logger.info(f"Error analyzed: {parsed['error_type']}")
            
            return {
                "success": True,
                "parsed_error": parsed,
                "diagnosis": diagnosis,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_correction(self, error_text: str, code: Optional[str] = None,
                      language: str = "python") -> Dict:
        """
        Get AI-powered correction suggestion
        
        Args:
            error_text: Error message or stack trace
            code: Problematic code snippet
            language: Programming language
        
        Returns:
            {"success": bool, "correction": str, "explanation": str, ...}
        """
        
        if not self.enabled:
            return {"success": False, "error": "Debugger not configured"}
        
        try:
            # First analyze error
            analysis = self.analyze_error(error_text, language)
            
            if not analysis.get("success"):
                return analysis
            
            parsed = analysis["parsed_error"]
            diagnosis = analysis["diagnosis"]
            
            # Build correction prompt
            code_section = f'Code with error:\n```{language}\n{code}\n```' if code else ''
            prompt = f"""You are an expert {language} debugger helping fix code errors.

Error Type: {parsed['error_type']}
Error Message: {parsed['error_message']}

Diagnosis:
- Likely Cause: {diagnosis['likely_cause']}
- Suggested Fixes: {', '.join(diagnosis['suggestions'])}

{code_section}

Please provide:
1. Root cause analysis
2. Step-by-step fix
3. Corrected code (if applicable)
4. Prevention tips"""
            
            import openai
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are an expert {language} debugger"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            correction = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "error_type": parsed["error_type"],
                "error_message": parsed["error_message"],
                "diagnosis": diagnosis,
                "correction": correction,
                "tokens_used": response.usage.total_tokens,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Correction error: {e}")
            return {"success": False, "error": str(e)}
    
    def set_breakpoint(self, file: str, line: int, condition: Optional[str] = None) -> Dict:
        """Set breakpoint"""
        
        breakpoint = {
            "id": len(self.breakpoints) + 1,
            "file": file,
            "line": line,
            "condition": condition,
            "enabled": True,
            "created": datetime.now().isoformat()
        }
        
        self.breakpoints.append(breakpoint)
        
        logger.info(f"Breakpoint set at {file}:{line}")
        
        return breakpoint
    
    def get_breakpoints(self) -> List[Dict]:
        """Get all breakpoints"""
        return self.breakpoints
    
    def remove_breakpoint(self, breakpoint_id: int):
        """Remove breakpoint"""
        self.breakpoints = [bp for bp in self.breakpoints if bp["id"] != breakpoint_id]
        logger.info(f"Breakpoint {breakpoint_id} removed")
    
    def add_watch(self, expression: str) -> Dict:
        """Add watch expression"""
        self.watches.append(expression)
        return {"watch": expression, "watches_count": len(self.watches)}
    
    def get_watches(self) -> List[str]:
        """Get all watches"""
        return self.watches
    
    def get_status(self) -> Dict:
        """Get debugger status"""
        return {
            "enabled": self.enabled,
            "breakpoints": len(self.breakpoints),
            "watches": len(self.watches),
            "provider": "OpenAI + Stack Trace Analysis"
        }


class VSCodeDebuggerManager:
    """Manages VS Code debugging"""
    
    def __init__(self):
        self.debugger = VSCodeDebugger()
        self.enabled = self.debugger.enabled
    
    def analyze_error(self, error: str, language: str = "python") -> Dict:
        """Analyze error"""
        return self.debugger.analyze_error(error, language)
    
    def get_correction(self, error: str, code: Optional[str] = None,
                      language: str = "python") -> Dict:
        """Get correction"""
        return self.debugger.get_correction(error, code, language)
    
    def set_breakpoint(self, file: str, line: int, condition: Optional[str] = None) -> Dict:
        """Set breakpoint"""
        return self.debugger.set_breakpoint(file, line, condition)
    
    def get_breakpoints(self) -> List[Dict]:
        """Get breakpoints"""
        return self.debugger.get_breakpoints()
    
    def get_status(self) -> Dict:
        """Get status"""
        return self.debugger.get_status()


# Need to import os
import os

# Global manager instance
vscode_debugger_manager = VSCodeDebuggerManager()


if __name__ == "__main__":
    # Demo
    print("VS Code Debugger Module")
    print("=" * 50)
    print(vscode_debugger_manager.get_status())
    print("\nUsage:")
    print("1. Analyze error: vscode_debugger_manager.analyze_error(error_text)")
    print("2. Get correction: vscode_debugger_manager.get_correction(error, code)")
    print("3. Set breakpoint: vscode_debugger_manager.set_breakpoint(file, line)")
