#!/usr/bin/env python3
"""
Direct test of APEX Environment core functionality (non-REST)
"""

from apex_env import APEXEnv, EnvironmentConfig
from apex_env import EmailAction, NoOpAction

print("\n" + "="*70)
print("APEX ENVIRONMENT - CORE FUNCTIONALITY TEST")
print("="*70 + "\n")

try:
    # Initialize environment
    print("1. Initializing APEXEnv...")
    config = EnvironmentConfig(max_episode_steps=10, seed=42)
    env = APEXEnv(config=config)
    print("   ✅ APEXEnv initialized")
    
    # Reset environment
    print("\n2. Resetting environment...")
    obs = env.reset()
    print(f"   ✅ Environment reset")
    print(f"      Observation type: {type(obs)}")
    
    # Execute actions
    print("\n3. Executing test actions...")
    
    # Test NoOp action
    print("   - Testing NoOp action...")
    result = env.step(NoOpAction(reason="test"))
    print(f"     ✅ Step executed")
    print(f"        Result type: {type(result)}")
    print(f"        Result has {len(result) if isinstance(result, tuple) else 1} values")
    if hasattr(result, 'reward'):
        print(f"        Reward: {result.reward}")
    elif isinstance(result, tuple) and len(result) >= 2:
        print(f"        Reward: {result[1]}")
    
    # Test Email action
    print("   - Testing Email action...")
    email_action = EmailAction(
        recipient_id=0,
        subject="Test Email",
        body="This is a test email",
        priority="medium",
        language="en"
    )
    result = env.step(email_action)
    print(f"     ✅ Email action executed")
    if hasattr(result, 'reward'):
        print(f"        Reward: {result.reward}")
    elif isinstance(result, tuple) and len(result) >= 2:
        print(f"        Reward: {result[1]}")
    
    # Get state
    print("\n4. Getting environment state...")
    state = env.state
    print(f"   ✅ State retrieved")
    print(f"      State type: {type(state)}")
    print(f"      Has email_system: {hasattr(state, 'email_system')}")
    
    print("\n" + "="*70)
    print("✅ ALL CORE FUNCTIONALITY TESTS PASSED")
    print("="*70 + "\n")
    
    # Close environment
    env.close()
    print("Environment closed successfully")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
