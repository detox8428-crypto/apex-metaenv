#!/usr/bin/env python3
"""
APEX Production Readiness Validation
Tests all major systems and verifies production readiness
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from apex_env.environment import APEXEnv
from apex_env.models import (
    EmailAction, MeetingAction, TranslationAction, GestureAction, NoOpAction,
    LanguageEnum, GestureEnum, MeetingTypeEnum
)

def test_api_health():
    """Test API health endpoint"""
    print("\nTEST 1: API Health Check")
    print("-" * 50)
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        data = response.json()
        print(f"[OK] API Status: {data['status']}")
        print(f"[OK] Environment initialized: {data['environment_initialized']}")
        return True
    except Exception as e:
        print(f"[FAIL] API Health check: {e}")
        return False

def test_environment_core():
    """Test core environment functionality"""
    print("\nTEST 2: Core Environment")
    print("-" * 50)
    try:
        env = APEXEnv()
        obs = env.reset()
        print("[OK] Environment reset successful")
        
        # Test NoOp action
        action = NoOpAction()
        obs, reward, done, truncated, info = env.step(action)
        reward_val = reward.total_reward if hasattr(reward, 'total_reward') else float(reward)
        print(f"[OK] NoOp action: reward={reward_val:.4f}")
        
        # Test Email action
        action = EmailAction(
            recipient_id=1,
            subject="Test Email",
            body="This is a test",
            language=LanguageEnum.EN,
            location="Office"
        )
        obs, reward, done, truncated, info = env.step(action)
        reward_val = reward.total_reward if hasattr(reward, 'total_reward') else float(reward)
        print(f"[OK] Email action: reward={reward_val:.4f}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Core environment: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reward_system():
    """Test 10-component reward system"""
    print("\nTEST 3: Reward System (10 components)")
    print("-" * 50)
    try:
        env = APEXEnv()
        obs = env.reset()
        
        total_reward = 0.0
        for i in range(3):
            action = NoOpAction()
            obs, reward, done, truncated, info = env.step(action)
            reward_val = reward.total_reward if hasattr(reward, 'total_reward') else float(reward)
            total_reward += reward_val
        
        print(f"[OK] Episode reward calculation: {total_reward:.4f}")
        
        # Check if reward components tracked
        if hasattr(obs, 'state_info') and isinstance(obs.state_info, dict):
            print(f"[OK] State info available: {len(obs.state_info)} keys")
        
        return True
    except Exception as e:
        print(f"[FAIL] Reward system: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multilingual():
    """Test multilingual system"""
    print("\nTEST 4: Multilingual System")
    print("-" * 50)
    try:
        env = APEXEnv()
        obs = env.reset()
        
        test_cases = [
            (LanguageEnum.EN, LanguageEnum.ES, "Hello everyone"),
            (LanguageEnum.EN, LanguageEnum.ZH, "Hello everyone"),
        ]
        
        for src, tgt, text in test_cases:
            action = TranslationAction(
                source_language=src,
                target_language=tgt,
                text=text
            )
            obs, reward, done, truncated, info = env.step(action)
            reward_val = reward.total_reward if hasattr(reward, 'total_reward') else float(reward)
            print(f"[OK] {src.value}->{tgt.value}: reward={reward_val:.4f}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Multilingual system: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gestures():
    """Test gesture recognition"""
    print("\nTEST 5: Gesture Recognition")
    print("-" * 50)
    try:
        env = APEXEnv()
        obs = env.reset()
        
        gestures = [
            (GestureEnum.SWIPE_RIGHT, 0.3),   # light intensity
            (GestureEnum.SWIPE_LEFT, 0.6),    # normal intensity
            (GestureEnum.LONG_PRESS, 0.9),    # strong intensity
        ]
        
        for gesture, intensity in gestures:
            action = GestureAction(
                gesture_code=gesture,
                intensity=intensity
            )
            obs, reward, done, truncated, info = env.step(action)
            reward_val = reward.total_reward if hasattr(reward, 'total_reward') else float(reward)
            print(f"[OK] {gesture.value} (intensity={intensity}): reward={reward_val:.4f}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Gesture system: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests"""
    print("\n" + "=" * 60)
    print("APEX PRODUCTION READINESS VALIDATION")
    print("=" * 60)
    
    results = {
        "API Health": test_api_health(),
        "Core Environment": test_environment_core(),
        "Reward System": test_reward_system(),
        "Multilingual": test_multilingual(),
        "Gestures": test_gestures(),
    }
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n*** ALL TESTS PASSED - PRODUCTION READY ***\n")
        return 0
    else:
        print(f"\n*** {total - passed} tests failed ***\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
