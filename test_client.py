"""Quick test script for Screen Task Environment"""

import time
import base64
from io import BytesIO
from PIL import Image
from screen_task_env.client import ScreenTaskEnvClient
from screen_task_env.models import ScreenAction


def test_environment():
    """Test the environment with a simple interaction"""
    print("=" * 60)
    print("Screen Task Environment - Quick Test")
    print("=" * 60)
    
    try:
        # Connect to server
        print("\n1. Connecting to server at http://localhost:8000...")
        client = ScreenTaskEnvClient("http://localhost:8000")
        print("   ✓ Connected")
        
        # Reset environment
        print("\n2. Resetting environment...")
        obs = client.reset()
        print(f"   ✓ Task: {obs.task}")
        print(f"   ✓ Step: {obs.step_num}")
        
        # Save initial screenshot
        try:
            img_data = base64.b64decode(obs.screenshot_b64)
            img = Image.open(BytesIO(img_data))
            img.save("screenshot_initial.png")
            print("   ✓ Screenshot saved: screenshot_initial.png")
        except Exception as e:
            print(f"   ⚠ Could not save screenshot: {e}")
        
        # Execute action: Type text
        print("\n3. Executing action: TYPE 'Hello World'")
        action = ScreenAction(
            action_type="type",
            text="Hello World"
        )
        
        obs, reward, done = client.step(action)
        print(f"   ✓ Action executed")
        print(f"   ✓ Reward: {reward}")
        print(f"   ✓ Done: {done}")
        print(f"   ✓ Feedback: {obs.last_action_result}")
        
        # Save result screenshot
        try:
            img_data = base64.b64decode(obs.screenshot_b64)
            img = Image.open(BytesIO(img_data))
            img.save("screenshot_after_action.png")
            print("   ✓ Screenshot saved: screenshot_after_action.png")
        except Exception as e:
            print(f"   ⚠ Could not save screenshot: {e}")
        
        # Try submit action
        if not done:
            print("\n4. Executing action: SUBMIT")
            submit_action = ScreenAction(action_type="submit")
            obs, reward, done = client.step(submit_action)
            print(f"   ✓ Submit executed")
            print(f"   ✓ Final Reward: {reward}")
            print(f"   ✓ Episode Done: {done}")
        
        print("\n" + "=" * 60)
        if done and reward > 0:
            print("✓ TEST PASSED - Environment working correctly!")
        else:
            print("⚠ Test completed but task not fully completed")
        print("=" * 60)
        
        # Cleanup
        client.close()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure server is running: python -m uvicorn server.app:app --host 0.0.0.0 --port 8000")
        print("2. Check Windows Firewall allows port 8000")
        print("3. Verify dependencies: pip install -e .")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_environment()
