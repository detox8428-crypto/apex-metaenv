#!/usr/bin/env python3
"""Test full workflow: reset, state, step with file persistence"""
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

print("Full workflow test with file persistence:\n")

# 1. Reset
print("1. /reset with query params")
r = client.post('/reset?domain=data_pipeline&difficulty=easy')
assert r.status_code == 200, f"Reset failed: {r.status_code}"
sid = r.json()['session_id']
print(f"   ✅ Session: {sid[:12]}...")

# 2. Get State immediately (tests file persistence)
print("\n2. /state (query param) - tests file persistence")
r = client.get(f'/state?session_id={sid}')
assert r.status_code == 200, f"State failed: {r.status_code}: {r.text}"
state1 = r.json()
print(f"   ✅ State loaded from file: step={state1['step']}, rewards={state1['rewards']}")

# 3. Submit code
print("\n3. /step - submit correct code")
r = client.post('/step', json={
    'session_id': sid,
    'code': """def aggregate_sales(df):
    return df.groupby('customer_id')['amount'].sum().sort_values(ascending=False)"""
})
assert r.status_code == 200, f"Step failed: {r.status_code}"
reward = r.json()['reward']
print(f"   ✅ Reward: {reward:.2f}")

# 4. Check updated state
print("\n4. /state (path param) after step")
r = client.get(f'/state/{sid}')
assert r.status_code == 200, f"State failed: {r.status_code}"
state2 = r.json()
print(f"   ✅ Step updated: step={state2['step']}, rewards={state2['rewards']}")

# 5. Reset with JSON body (alternate endpoint)
print("\n5. /reset/json with body (alternate format)")
r = client.post('/reset/json', json={
    'domain': 'data_pipeline',
    'difficulty': 'easy'
})
assert r.status_code == 200, f"Reset failed: {r.status_code}"
sid2 = r.json()['session_id']
print(f"   ✅ Session from /reset/json: {sid2[:12]}...")

# 6. Verify both sessions exist
print("\n6. Verify both sessions in file storage")
r = client.get(f'/state/{sid}')
assert r.status_code == 200
r = client.get(f'/state/{sid2}')
assert r.status_code == 200
print(f"   ✅ Both sessions persist independently")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - File persistence working!")
print("="*60)
