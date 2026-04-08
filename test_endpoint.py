#!/usr/bin/env python3
"""
Test the actual /reset endpoint to diagnose the issue
"""

import requests
import json

BASE = "https://shaikb-apex.hf.space"

print("Testing /reset endpoint variations...")
print()

# Test 1: Query params only, with empty body
print("TEST 1: Query params + empty body")
try:
    r = requests.post(
        f"{BASE}/reset?domain=data_pipeline&difficulty=easy",
        headers={"Content-Length": "0"},
        timeout=15
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        print(f"  ✅ Got session_id: {r.json().get('session_id', 'N/A')[:8]}...")
    else:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 2: JSON body with all params
print()
print("TEST 2: JSON body")
try:
    r = requests.post(
        f"{BASE}/reset",
        json={"domain": "data_pipeline", "difficulty": "easy"},
        timeout=15
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        print(f"  ✅ Got session_id: {r.json().get('session_id', 'N/A')[:8]}...")
    else:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: Query params with explicit empty dict body
print()
print("TEST 3: Query params + empty dict body")
try:
    r = requests.post(
        f"{BASE}/reset?domain=data_pipeline&difficulty=easy",
        json={},
        timeout=15
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        print(f"  ✅ Got session_id: {r.json().get('session_id', 'N/A')[:8]}...")
    else:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 4: Root and health endpoints
print()
print("TEST 4: Root endpoint")
try:
    r = requests.get(f"{BASE}/", timeout=15)
    print(f"  Status: {r.status_code}")
    print(f"  Has 'endpoints': {'endpoints' in r.json()}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("TEST 5: Health endpoint")
try:
    r = requests.get(f"{BASE}/health", timeout=15)
    print(f"  Status: {r.status_code}")
    print(f"  Active sessions: {r.json().get('active_sessions', 'N/A')}")
except Exception as e:
    print(f"  Error: {e}")
