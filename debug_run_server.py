#!/usr/bin/env python3
"""
Debug script to check what app is actually being loaded
"""

import sys
import os
from pathlib import Path

# Get project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Python version: {sys.version}")
print(f"\nPython path:")
for i, p in enumerate(sys.path[:5]):
    print(f"  {i}: {p}")

# Try importing server
print(f"\nImporting server...")
import server
print(f"server module file: {server.__file__}")
print(f"server.app: {server.app}")
print(f"server.app.__class__: {server.app.__class__}")

# Check if it's the right app
from fastapi import FastAPI
print(f"Is FastAPI app: {isinstance(server.app, FastAPI)}")

# Print info about the app
schema = server.app.openapi()
print(f"\nApp Info:")
print(f"  Title: {schema.get('info', {}).get('title')}")
print(f"  Version: {schema.get('info', {}).get('version')}")

paths = list(schema.get('paths', {}).keys())
print(f"\nPaths ({len(paths)}):")
for path in sorted(paths):
    print(f"  {path}")

# Now test running uvicorn with this app
print(f"\n{'='*70}")
print("Starting uvicorn with the app...")
print(f"{'='*70}\n")

import uvicorn
uvicorn.run(
    server.app,
    host="0.0.0.0",
    port=8001,
    log_level="info",
)
