#!/usr/bin/env python3
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

print("Testing /reset endpoint...")

# Test 1: Query params only
print('\nTEST 1: /reset with query params only')
r = client.post('/reset?domain=data_pipeline&difficulty=easy')
print(f'  Status: {r.status_code}')
if r.status_code == 200:
    print(f'  ✅ PASS - session created')
else:
    print(f'  ❌ FAIL - {r.text[:200]}')

# Test 2: JSON body only  
print('\nTEST 2: /reset with JSON body')
r = client.post('/reset', json={'domain': 'data_pipeline', 'difficulty': 'easy'})
print(f'  Status: {r.status_code}')
if r.status_code == 200:
    print(f'  ✅ PASS - session created')
else:
    print(f'  ❌ FAIL - {r.text[:200]}')

# Test 3: Default query params (no params passed)
print('\nTEST 3: /reset with no parameters (defaults)')
r = client.post('/reset')
print(f'  Status: {r.status_code}')
if r.status_code == 200:
    print(f'  ✅ PASS - session created with defaults')
else:
    print(f'  ❌ FAIL - {r.text[:200]}')
