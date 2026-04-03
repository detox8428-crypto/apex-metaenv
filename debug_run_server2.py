#!/usr/bin/env python3
"""
Debug version of run_server.py to trace the issue
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
    
    print(f"\n[DEBUG] Project root: {project_root}")
    print(f"[DEBUG] sys.path[0]: {sys.path[0]}")
    
    # Load configuration
    print(f"\n[DEBUG] Loading configuration...")
    try:
        from config import ConfigLoader
        print(f"[DEBUG] ConfigLoader imported: {ConfigLoader}")
        config = ConfigLoader.load_config()
        print(f"[DEBUG] Config loaded: {type(config)}")
        server_config = ConfigLoader.get_server_config(config)
        print(f"[DEBUG] Server config: {server_config}")
    except Exception as e:
        print(f"[WARNING] Failed to load config: {e}")
        import traceback
        traceback.print_exc()
        server_config = {"host": "0.0.0.0", "port": 8000}
    
    # Extract server config
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    
    print(f"\n[DEBUG] Importing server module...")
    # Import app
    try:
        from server import app
        print(f"[DEBUG] server module imported: {os.path.abspath('server.py')}")
        print(f"[DEBUG] app object: {app}")
        print(f"[DEBUG] app class: {app.__class__}")
        
        # Check the app's endpoints
        schema = app.openapi()
        title = schema.get('info', {}).get('title')
        paths = list(schema.get('paths', {}).keys())
        print(f"[DEBUG] App title: {title}")
        print(f"[DEBUG] Paths: {sorted(paths)}")
        
    except ImportError as e:
        print(f"[ERROR] Error importing server: {e}")
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
