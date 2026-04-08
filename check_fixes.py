#!/usr/bin/env python3
"""
Validation script for APEX bug fixes
Tests all critical fixes on the live HF Space
"""

import requests
import time

BASE = "https://shaikb-apex.hf.space"
print("=" * 70)
print("APEX CRITICAL BUG FIX VALIDATION")
print("=" * 70)
print()

# Wait for HF Space rebuild
print("⏳ Waiting 40s for HF Space to rebuild...")
time.sleep(40)

# 1. Test /reset with query params
print("TEST 1: /reset with query params (new feature)")
try:
    r = requests.post(f"{BASE}/reset?domain=data_pipeline&difficulty=easy", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    sid1 = r.json()["session_id"]
    print(f"  ✅ PASS | session={sid1[:8]}...")
except Exception as e:
    print(f"  ❌ FAIL | {e}")
    exit(1)

# 2. Test /state with query param (should NOT return 404 anymore)
print("TEST 2: /state with query param (BUG FIX #1 - session persistence)")
try:
    r = requests.get(f"{BASE}/state?session_id={sid1}", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    state_data = r.json()
    assert state_data["session_id"] == sid1
    print(f"  ✅ PASS | Session persisted across requests (file-based storage)")
except Exception as e:
    print(f"  ❌ FAIL | {e}")
    exit(1)

# 3. Test bad code returns LOW reward (BUG FIX #2)
print("TEST 3: Bad code (empty/minimal) returns low reward (BUG FIX #2)")
try:
    r = requests.post(f"{BASE}/reset", json={"domain": "data_pipeline", "difficulty": "easy"}, timeout=10)
    sid2 = r.json()["session_id"]
    
    r = requests.post(f"{BASE}/step", json={
        "session_id": sid2,
        "code": "# nothing"
    }, timeout=10)
    
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    reward = r.json()["reward"]
    print(f"  Bad code reward: {reward}")
    assert reward < 0.4, f"Bad code should return <0.4, got {reward}"
    print(f"  ✅ PASS | Bad code reward {reward:.2f} is correctly LOW")
except Exception as e:
    print(f"  ❌ FAIL | {e}")
    exit(1)

# 4. Test good code returns HIGH reward
print("TEST 4: Correct code returns high reward (BUG FIX #2)")
try:
    r = requests.post(f"{BASE}/reset", json={"domain": "data_pipeline", "difficulty": "easy"}, timeout=10)
    sid3 = r.json()["session_id"]
    
    # Use CORRECT function name: aggregate_sales (not solve)
    r = requests.post(f"{BASE}/step", json={
        "session_id": sid3,
        "code": "def aggregate_sales(df):\n    return df.groupby('customer_id')['amount'].sum().sort_values(ascending=False)"
    }, timeout=10)
    
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    reward = r.json()["reward"]
    print(f"  Correct code reward: {reward}")
    assert reward > 0.5, f"Correct code should return >0.5, got {reward}"
    print(f"  ✅ PASS | Correct code reward {reward:.2f} is HIGH")
except Exception as e:
    print(f"  ❌ FAIL | {e}")
    exit(1)

# 5. Test deterministic scoring (same code = same reward)
print("TEST 5: Deterministic scoring (same code = same reward)")
try:
    rewards = []
    for attempt in range(2):
        r = requests.post(f"{BASE}/reset", json={"domain": "data_pipeline", "difficulty": "easy"}, timeout=10)
        sid = r.json()["session_id"]
        
        r = requests.post(f"{BASE}/step", json={
            "session_id": sid,
            "code": "def solve(df):\n    return df.head(3)"
        }, timeout=10)
        
        reward = r.json()["reward"]
        rewards.append(reward)
    
    assert rewards[0] == rewards[1], f"Same code should give same reward: {rewards[0]} vs {rewards[1]}"
    print(f"  ✅ PASS | Deterministic: {rewards[0]:.2f} == {rewards[1]:.2f}")
except Exception as e:
    print(f"  ❌ FAIL | {e}")
    exit(1)

# 6. Test /state with path param also works
print("TEST 6: /state with path param (backwards compatibility)")
try:
    r = requests.post(f"{BASE}/reset", json={"domain": "data_pipeline", "difficulty": "easy"}, timeout=10)
    sid4 = r.json()["session_id"]
    
    r = requests.get(f"{BASE}/state/{sid4}", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    print(f"  ✅ PASS | Path parameter /state/{{id}} works")
except Exception as e:
    print(f"  ❌ FAIL | {e}")
    exit(1)

# 7. Test /reset with JSON body still works
print("TEST 7: /reset with JSON body (backwards compatibility)")
try:
    r = requests.post(f"{BASE}/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy"
    }, timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print(f"  ✅ PASS | JSON body still works")
except Exception as e:
    print(f"  ❌ FAIL | {e}")
    exit(1)

print()
print("=" * 70)
print("✅ ALL VALIDATION TESTS PASSED!")
print("=" * 70)
print()
print("Summary of fixes:")
print("  BUG 1: File-based sessions (persistence across workers) ✅")
print("  BUG 2: Stricter graders with correct reward bounds ✅")
print("  BONUS: Support both query params and JSON body ✅")
print()
print("The APEX Space is now ready for production submission!")
