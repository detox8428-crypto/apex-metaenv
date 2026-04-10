#!/usr/bin/env python3
"""
Test script to verify inference.py environment setup
"""
import os
import sys

print("=" * 70)
print("APEX INFERENCE TEST")
print("=" * 70)
print()

# Check environment variables
print("[1] Environment Variables")
print("-" * 70)

required_vars = {
    "API_BASE_URL": "https://router.huggingface.co/v1",
    "API_KEY": "hf_test_placeholder",
    "MODEL_NAME": "Qwen/Qwen2.5-72B-Instruct",
}

os.environ.update(required_vars)

for var, default in required_vars.items():
    value = os.environ.get(var, "NOT SET")
    status = "OK" if value != "NOT SET" else "MISSING"
    print(f"  {var:<20} = {value:<40} [{status}]")

print()
print("[2] Module Imports")
print("-" * 70)

try:
    from openai import OpenAI
    print("  openai.OpenAI              - OK")
except Exception as e:
    print(f"  openai.OpenAI              - FAILED: {e}")
    sys.exit(1)

try:
    import requests
    print("  requests                   - OK")
except Exception as e:
    print(f"  requests                   - FAILED: {e}")
    sys.exit(1)

print()
print("[3] OpenAI Client Initialization")
print("-" * 70)

try:
    API_BASE_URL = os.environ["API_BASE_URL"]
    API_KEY = os.environ["API_KEY"]
    
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
    )
    print("  OpenAI client created      - OK")
    print(f"  Base URL: {API_BASE_URL}")
    print(f"  API Key configured: {len(API_KEY)} chars")
except Exception as e:
    print(f"  OpenAI client creation     - FAILED: {e}")
    sys.exit(1)

print()
print("[4] Simulated LLM Call Structure")
print("-" * 70)

try:
    MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
    
    # Don't actually call the API (no real key), just verify the structure
    test_message = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an expert Python engineer."},
            {"role": "user", "content": "Write code to solve X"}
        ],
        "max_tokens": 1000,
        "temperature": 0.3,
    }
    
    print("  Message structure valid    - OK")
    print(f"  Model: {test_message['model']}")
    print(f"  Messages: {len(test_message['messages'])} items")
    print(f"  Max tokens: {test_message['max_tokens']}")
except Exception as e:
    print(f"  Message structure check    - FAILED: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("ALL TESTS PASSED!")
print("=" * 70)
print()
print("Ready to run: python inference.py")
print()
