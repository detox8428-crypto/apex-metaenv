"""
Validation script to ensure all imports and basic functionality work
"""

import sys
from datetime import datetime, timedelta


def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    try:
        from apex_env import (
            APEXEnv,
            EnvironmentConfig,
            EmailAction,
            MeetingAction,
            TranslationAction,
            GestureAction,
            LanguageEnum,
            PriorityEnum,
            MeetingTypeEnum,
            GestureEnum,
        )
        from apex_env.state import Contact, Task
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_environment_creation():
    """Test basic environment creation and reset"""
    print("\nTesting environment creation...")
    try:
        from apex_env import APEXEnv, EnvironmentConfig
        
        config = EnvironmentConfig(
            max_episode_steps=100,
            seed=42,
        )
        env = APEXEnv(config=config)
        obs = env.reset()
        
        assert obs is not None, "Observation is None"
        assert len(env.state.contacts) > 0, "No contacts initialized"
        print(f"✓ Environment created with {len(env.state.contacts)} contacts")
        return True
    except Exception as e:
        print(f"✗ Environment creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_action():
    """Test email action"""
    print("\nTesting email action...")
    try:
        from apex_env import APEXEnv, EnvironmentConfig, EmailAction, PriorityEnum, LanguageEnum
        
        env = APEXEnv(config=EnvironmentConfig(seed=42))
        env.reset()
        
        action = EmailAction(
            recipient_id=0,
            subject="Test Email",
            body="This is a test email body.",
            priority=PriorityEnum.HIGH,
            language=LanguageEnum.EN,
        )
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        assert info['action_result']['success'], "Email action failed"
        assert obs.email_status.sent_count > 0, "Email not recorded"
        assert reward.total_reward > -1, "Reward out of range"
        
        print(f"✓ Email action successful, reward={reward.total_reward:.3f}")
        return True
    except Exception as e:
        print(f"✗ Email action test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_meeting_action():
    """Test meeting scheduling"""
    print("\nTesting meeting action...")
    try:
        from apex_env import APEXEnv, EnvironmentConfig, MeetingAction, MeetingTypeEnum
        
        env = APEXEnv(config=EnvironmentConfig(seed=42))
        env.reset()
        
        action = MeetingAction(
            title="Test Meeting",
            attendee_ids=[0, 1, 2],
            scheduled_time=datetime.utcnow() + timedelta(days=1),
            duration_minutes=60,
            meeting_type=MeetingTypeEnum.VIRTUAL,
            location=None,
            description=None,
        )
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        assert info['action_result']['success'], "Meeting action failed"
        assert obs.calendar_status.meeting_count > 0, "Meeting not recorded"
        
        print(f"✓ Meeting action successful, reward={reward.total_reward:.3f}")
        return True
    except Exception as e:
        print(f"✗ Meeting action test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_translation_action():
    """Test translation action"""
    print("\nTesting translation action...")
    try:
        from apex_env import APEXEnv, EnvironmentConfig, TranslationAction, LanguageEnum
        
        env = APEXEnv(config=EnvironmentConfig(seed=42))
        env.reset()
        
        action = TranslationAction(
            text="Hello, how are you?",
            source_language=LanguageEnum.EN,
            target_language=LanguageEnum.ES,
        )
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        assert info['action_result']['success'], "Translation action failed"
        assert len(env.state.translation_history) > 0, "Translation not recorded"
        
        print(f"✓ Translation action successful, reward={reward.total_reward:.3f}")
        return True
    except Exception as e:
        print(f"✗ Translation action test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gesture_action():
    """Test gesture recognition"""
    print("\nTesting gesture action...")
    try:
        from apex_env import APEXEnv, EnvironmentConfig, GestureAction, GestureEnum
        
        env = APEXEnv(config=EnvironmentConfig(seed=42))
        env.reset()
        
        action = GestureAction(
            gesture_code=GestureEnum.SWIPE_RIGHT,
            intensity=0.75,
        )
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        assert info['action_result']['success'], "Gesture action failed"
        assert len(env.state.gesture_history) > 0, "Gesture not recorded"
        
        print(f"✓ Gesture action successful, reward={reward.total_reward:.3f}")
        return True
    except Exception as e:
        print(f"✗ Gesture action test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_step_episode():
    """Test multi-step episode"""
    print("\nTesting multi-step episode...")
    try:
        from apex_env import (
            APEXEnv, EnvironmentConfig, 
            EmailAction, MeetingAction, LanguageEnum, MeetingTypeEnum
        )
        
        env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5, seed=42))
        env.reset()
        
        actions = [
            EmailAction(
                recipient_id=0,
                subject="Test",
                body="Test body",
                language=LanguageEnum.EN,
            ),
            MeetingAction(
                title="Test",
                attendee_ids=[0, 1],
                scheduled_time=datetime.utcnow() + timedelta(days=1),
                duration_minutes=30,
                location=None,
                description=None,
            ),
        ]
        
        for i, action in enumerate(actions):
            obs, reward, terminated, truncated, info = env.step(action)
            assert not terminated, f"Episode terminated at step {i}"
        
        assert env._steps_taken == len(actions), "Step count mismatch"
        
        print(f"✓ Multi-step episode successful, {env._steps_taken} steps completed")
        return True
    except Exception as e:
        print(f"✗ Multi-step episode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("=" * 70)
    print("APEX ENVIRONMENT VALIDATION")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_environment_creation,
        test_email_action,
        test_meeting_action,
        test_translation_action,
        test_gesture_action,
        test_multi_step_episode,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Unexpected error in {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if all(results):
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
