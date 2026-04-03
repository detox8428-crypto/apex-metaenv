#!/usr/bin/env python3
"""
FastAPI Server Startup Script

Launcher for the APEX Environment API server.
Run with: python run_server.py
"""

import sys
import os
import uvicorn
from pathlib import Path

def main():
    """Run the server"""
    # Get project root
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Load configuration
    try:
        from config import ConfigLoader
        config = ConfigLoader.load_config()
        server_config = ConfigLoader.get_server_config(config)
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        print("Using default configuration")
        server_config = {"host": "0.0.0.0", "port": 8000}
    
    # Extract server config
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    
    # Import app
    try:
        from server import app
    except ImportError as e:
        print(f"Error importing server: {e}")
        print("Make sure server.py is in the same directory")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("APEX ENVIRONMENT - FastAPI Server")
    print("=" * 70)
    print(f"Starting server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print()
    print("📖 Interactive docs: http://localhost:{}/docs".format(port))
    print("📖 Alternative docs: http://localhost:{}/redoc".format(port))
    print()
    print("Environment variables:")
    print(f"  API_BASE_URL: {os.getenv('API_BASE_URL', 'not set')}")
    print(f"  MODEL_NAME: {os.getenv('MODEL_NAME', 'not set')}")
    print()
    print("Press CTRL+C to stop")
    print("=" * 70 + "\n")
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )

if __name__ == "__main__":
    main()
