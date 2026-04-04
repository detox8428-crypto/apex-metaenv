"""Sandboxed code execution with security checks"""

import ast
import subprocess
import tempfile
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import resource module (POSIX only)
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("resource module not available (Linux/Mac only) - resource limits disabled")

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when code violates security constraints"""
    pass


class ExecutionError(Exception):
    """Raised when code execution fails"""
    pass


class ASTSecurityChecker:
    """Static AST-based security checker for submitted code"""

    # Blocked module imports
    BLOCKED_IMPORTS = {
        'os', 'subprocess', 'socket', 'requests', 'urllib',
        'http', 'ftplib', 'telnetlib', 'smtplib', 'poplib',
        '__main__', 'sys', 'ctypes', 'linecache', 'inspect',
        'importlib', 'pkgutil', 'runpy', 'code', 'codeop'
    }

    # Blocked built-in functions
    BLOCKED_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open',
        'input', 'raw_input'
    }

    def __init__(self):
        """Initialize the security checker"""
        self.errors = []

    def check(self, code: str) -> None:
        """
        Check code for security violations using AST analysis
        
        Args:
            code: The Python code to check
            
        Raises:
            SecurityError: If any violation is found
        """
        self.errors = []
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # Syntax errors are OK, let them execute and fail normally
            return

        self._check_tree(tree)

        if self.errors:
            raise SecurityError("; ".join(self.errors))

    def _check_tree(self, node: ast.AST) -> None:
        """Recursively check AST nodes"""
        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                self._check_import(child)
            elif isinstance(child, ast.ImportFrom):
                self._check_import_from(child)
            elif isinstance(child, ast.Call):
                self._check_call(child)
            elif isinstance(child, ast.Attribute):
                self._check_attribute(child)

    def _check_import(self, node: ast.Import) -> None:
        """Check import statement"""
        for alias in node.names:
            module = alias.name.split('.')[0]
            if module in self.BLOCKED_IMPORTS:
                self.errors.append(
                    f"Import of blocked module '{module}' not allowed"
                )

    def _check_import_from(self, node: ast.ImportFrom) -> None:
        """Check from...import statement"""
        if node.module:
            module = node.module.split('.')[0]
            if module in self.BLOCKED_IMPORTS:
                self.errors.append(
                    f"Import from blocked module '{module}' not allowed"
                )

    def _check_call(self, node: ast.Call) -> None:
        """Check function calls"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.BLOCKED_BUILTINS:
                self.errors.append(
                    f"Calling blocked function '{func_name}' not allowed"
                )

    def _check_attribute(self, node: ast.Attribute) -> None:
        """Check attribute access (e.g., __class__.__bases__)"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        # Check for dangerous attribute chains
        if '__' in ''.join(parts):
            self.errors.append(
                f"Access to dunder attributes not allowed"
            )


def set_resource_limits():
    """
    Set resource limits for the subprocess.
    
    - CPU: 10 seconds
    - Memory: 256 MB
    - File size: 0 bytes (no writing)
    - Processes: 1 (no subprocess spawning)
    
    Note: Resource limits only work on POSIX systems (Linux/Mac).
    On Windows, this function will log a warning and return without setting limits.
    """
    if not HAS_RESOURCE:
        logger.debug("Resource module not available - skipping resource limit configuration")
        return
    
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    except (ValueError, AttributeError):
        logger.warning("Could not set CPU limit (may not be available on this platform)")

    try:
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    except (ValueError, AttributeError):
        logger.warning("Could not set memory limit")

    try:
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    except (ValueError, AttributeError):
        logger.warning("Could not set file size limit")

    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
    except (ValueError, AttributeError):
        logger.warning("Could not set process limit")


def create_test_harness(code: str, test_cases: list[Dict[str, Any]], func_name: str) -> str:
    """
    Create a test harness that executes code and test cases in a sandbox.
    
    Args:
        code: The submitted solution code
        test_cases: List of test cases with 'input' and 'expected' keys
        func_name: Name of the function to test
        
    Returns:
        Complete Python code including harness
    """
    # Serialize test cases to JSON
    test_cases_json = json.dumps(test_cases)

    harness = f'''
import sys
import json
import time

# ===== USER CODE =====
{code}
# ===== END USER CODE =====

# ===== TEST HARNESS =====
test_cases = json.loads("""{test_cases_json}""")
results = []

for case_idx, case in enumerate(test_cases):
    try:
        test_input = case["input"]
        expected = case["expected"]
        
        start_time = time.time()
        
        # Call the function
        if isinstance(test_input, dict):
            actual = {func_name}(**test_input)
        elif isinstance(test_input, (list, tuple)):
            actual = {func_name}(*test_input)
        else:
            actual = {func_name}(test_input)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Check result
        passed = (actual == expected)
        
        results.append({{
            "case_index": case_idx,
            "passed": passed,
            "error": None,
            "time_ms": elapsed_ms
        }})
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
        results.append({{
            "case_index": case_idx,
            "passed": False,
            "error": str(e),
            "time_ms": elapsed_ms
        }})

# Output results as JSON
print(json.dumps({{"results": results}}))
'''
    return harness


def execute_code_sandboxed(
    code: str,
    test_cases: list[Dict[str, Any]],
    func_name: str,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Execute submitted code in a sandboxed subprocess.
    
    Args:
        code: The Python code to execute
        test_cases: List of test cases
        func_name: Name of the function to test
        timeout: Execution timeout in seconds
        
    Returns:
        Dictionary with execution results:
        {
            "results": [{"case_index": int, "passed": bool, "error": str|null, "time_ms": float}],
            "error": str|null,
            "error_type": str|null
        }
    """
    # Step 1: Static security check
    try:
        checker = ASTSecurityChecker()
        checker.check(code)
    except SecurityError as e:
        return {
            "results": [],
            "error": f"SECURITY_VIOLATION: {str(e)}",
            "error_type": "SECURITY",
            "passed_count": 0
        }

    # Step 2: Create test harness
    try:
        harness = create_test_harness(code, test_cases, func_name)
    except Exception as e:
        return {
            "results": [],
            "error": f"Failed to create test harness: {str(e)}",
            "error_type": "HARNESS",
            "passed_count": 0
        }

    # Step 3: Write to temp file and execute
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(harness)
            temp_file = f.name

        # Run subprocess with resource limits
        result = subprocess.run(
            [sys.executable, "-u", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            preexec_fn=set_resource_limits if sys.platform != 'win32' else None
        )

        # Parse output
        try:
            output = json.loads(result.stdout)
            results = output.get("results", [])

            # Count passed cases
            passed_count = sum(1 for r in results if r.get("passed"))

            return {
                "results": results,
                "error": None,
                "error_type": None,
                "passed_count": passed_count
            }
        except json.JSONDecodeError:
            # Code execution failed or produced invalid JSON
            error_msg = result.stderr or result.stdout or "Unknown error"
            return {
                "results": [],
                "error": f"RUNTIME_ERROR: {error_msg}",
                "error_type": "RUNTIME",
                "passed_count": 0
            }

    except subprocess.TimeoutExpired:
        return {
            "results": [],
            "error": "TIMEOUT: Code execution exceeded 10 seconds",
            "error_type": "TIMEOUT",
            "passed_count": 0
        }
    except Exception as e:
        return {
            "results": [],
            "error": f"EXECUTION_ERROR: {str(e)}",
            "error_type": "EXECUTION",
            "passed_count": 0
        }
    finally:
        # Clean up temp file
        if temp_file:
            try:
                Path(temp_file).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")
