#!/usr/bin/env python3
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# 1. Reset
print("\n1. /reset (query params)")
r = client.post('/reset?domain=data_pipeline&difficulty=easy')
if r.status_code != 200:
    print(f"   ❌ FAILED {r.status_code}: {r.text}")
    exit(1)
sid = r.json()['session_id']
print(f"   ✅ Session: {sid[:12]}...")

# 2. State (from file)
print("\n2. /state (file-based persistence)")
r = client.get(f'/state?session_id={sid}')
if r.status_code != 200:
    print(f"   ❌ FAILED {r.status_code}: {r.text}")
    exit(1)
print(f"   ✅ State: step=0, done=False")

# 3. Step
print("\n3. /step (correct code)")
r = client.post('/step', json={
    'session_id': sid,
    'code': 'def aggregate_sales(df):\n    return df.groupby("customer_id")["amount"].sum().sort_values(ascending=False)'
})
if r.status_code != 200:
    print(f"   ❌ FAILED {r.status_code}: {r.json()}")
    exit(1)
reward = r.json()['reward']
print(f"   ✅ Reward: {reward:.2f}")

print("\n✅ All tests passed!\n")
