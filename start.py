#!/usr/bin/env python3
"""
APEX Production Startup Script

Validates environment and starts the server.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Validate and start server."""
    project_root = Path(__file__).parent
    
    print("\n" + "=" * 70)
    print("APEX ENVIRONMENT - PRODUCTION STARTUP")
    print("=" * 70 + "\n")
    
    # Run validation
    print("Running pre-flight validation...")
    validation_result = subprocess.run(
        [sys.executable, str(project_root / "validate_production.py")],
        cwd=str(project_root)
    )
    
    if validation_result.returncode != 0:
        print("\n" + "=" * 70)
        print("❌ Validation failed. Cannot start server.")
        print("=" * 70 + "\n")
        return 1
    
    print("\n" + "=" * 70)
    print("✓ Validation passed. Starting FastAPI server...")
    print("=" * 70 + "\n")
    
    # Start server
    server_result = subprocess.run(
        [sys.executable, str(project_root / "run_server.py")],
        cwd=str(project_root)
    )
    
    return server_result.returncode


if __name__ == "__main__":
    sys.exit(main())
