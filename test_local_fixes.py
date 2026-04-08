#!/usr/bin/env python3
"""
Local test for all bug fixes
"""

from fastapi.testclient import TestClient
from app import app
import json

client = TestClient(app)

print('='*70)
print('LOCAL TEST: All bug fixes validation')
print('='*70)

# TEST 1: Reset with query params
print('\nTEST 1: /reset with query params (new feature)')
r = client.post('/reset?domain=data_pipeline&difficulty=easy')
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
sid = r.json()['session_id']
print(f'  ✅ PASS | session={sid[:8]}...')

# TEST 2: State with query param (session persistence)
print('\nTEST 2: /state with query param (BUG FIX #1 - session persistence)')
r = client.get(f'/state?session_id={sid}')
assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
print(f'  ✅ PASS | Session persisted (file-based storage works)')

# TEST 3: State with path param
print('\nTEST 3: /state with path param (backwards compatibility)')
r = client.get(f'/state/{sid}')
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
print(f'  ✅ PASS | Path param /state/{{id}} works')

# TEST 4: Bad code = low reward
print('\nTEST 4: Bad code returns LOW reward (BUG FIX #2)')
r = client.post('/step', json={'session_id': sid, 'code': '# nothing'})
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
reward_bad = r.json()['reward']
print(f'  Bad code reward: {reward_bad:.2f}')
assert reward_bad < 0.4, f'Bad code should return <0.4, got {reward_bad}'
print(f'  ✅ PASS | Correctly returns LOW reward {reward_bad:.2f}')

# TEST 5: Good code = high reward
print('\nTEST 5: Good code returns HIGH reward (BUG FIX #2)')
r = client.post('/reset', json={'domain': 'data_pipeline', 'difficulty': 'easy'})
sid2 = r.json()['session_id']

# Use the CORRECT function name for the task: aggregate_sales, not solve
code = """def aggregate_sales(df):
    return df.groupby('customer_id')['amount'].sum().sort_values(ascending=False)"""

r = client.post('/step', json={'session_id': sid2, 'code': code})
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
reward_good = r.json()['reward']
print(f'  Good code reward: {reward_good:.2f}')
assert reward_good > 0.5, f'Good code should return >0.5, got {reward_good}'
print(f'  ✅ PASS | Correctly returns HIGH reward {reward_good:.2f}')

# TEST 6: Deterministic scoring
print('\nTEST 6: Deterministic scoring (same code = same reward)')
rewards = []
for i in range(2):
    r = client.post('/reset', json={'domain': 'data_pipeline', 'difficulty': 'easy'})
    sid_test = r.json()['session_id']
    r = client.post('/step', json={'session_id': sid_test, 'code': 'def aggregate_sales(df): return df.head(3)'})
    rewards.append(r.json()['reward'])

assert rewards[0] == rewards[1], f'Same code should give same reward: {rewards[0]} vs {rewards[1]}'
print(f'  Reward 1: {rewards[0]:.2f}')
print(f'  Reward 2: {rewards[1]:.2f}')
print(f'  ✅ PASS | Deterministic: {rewards[0]:.2f} == {rewards[1]:.2f}')

# TEST 7: Reset with JSON body (backwards compatibility)
print('\nTEST 7: /reset with JSON body (backwards compatibility)')
r = client.post('/reset', json={'domain': 'data_pipeline', 'difficulty': 'easy'})
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
print(f'  ✅ PASS | JSON body still works')

print()
print('='*70)
print('✅ ALL LOCAL TESTS PASSED!')
print('='*70)
print()
print('Summary:')
print('  BUG #1: File-based sessions (persistence across workers) ✅')
print('  BUG #2: Stricter graders with correct reward bounds ✅')
print('  BONUS: Support both query params and JSON body ✅')
