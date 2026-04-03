"""
Quick test to verify email integration is working correctly
"""

import requests
import json

def test_email_action():
    """Test sending an email action through the API"""
    
    BASE_URL = "http://localhost:8000"
    
    print("=" * 60)
    print("APEX EMAIL INTEGRATION TEST")
    print("=" * 60)
    
    # Reset environment first
    print("\n[SETUP] Resetting environment...")
    try:
        reset_body = {"seed": 42, "max_episode_steps": 100}
        response = requests.post(f"{BASE_URL}/reset", json=reset_body, timeout=5)
        if response.status_code == 200:
            print("✓ Environment reset successful")
        else:
            print(f"⚠ Reset warning (status {response.status_code})")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Reset failed: {str(e)}")
        return
    
    # Test 1: Simulated Email (default)
    print("\n[TEST 1] Sending simulated email...")
    action_data = {
        "action_type": "email",
        "recipient_id": 1,
        "subject": "Test Email - Simulated",
        "body": "This is a test email from APEX",
        "language": "EN",
        "location": "Office",
        "send_real": False
    }
    
    request_body = {"action": action_data}
    
    try:
        response = requests.post(
            f"{BASE_URL}/step",
            json=request_body,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ SUCCESS (Status: {response.status_code})")
            print(f"  Mode: {result.get('details', {}).get('mode', 'unknown')}")
            print(f"  Reward: {result.get('reward', {}).get('total_reward', 0):.4f}")
            print(f"  Real Email Sent: {result.get('details', {}).get('real_email_sent', False)}")
        else:
            print(f"✗ FAILED (Status: {response.status_code})")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    # Test 2: Real Email (with send_real flag)
    print("\n[TEST 2] Attempting real email (if credentials configured)...")
    action_real_data = {
        "action_type": "email",
        "recipient_id": 1,
        "subject": "Test Email - Real Attempt",
        "body": "This would be a real email if credentials are configured",
        "language": "EN",
        "location": "Office",
        "send_real": True
    }
    
    request_body_real = {"action": action_real_data}
    
    try:
        response = requests.post(
            f"{BASE_URL}/step",
            json=request_body_real,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ SUCCESS (Status: {response.status_code})")
            print(f"  Mode: {result.get('details', {}).get('mode', 'unknown')}")
            print(f"  Real Email Sent: {result.get('details', {}).get('real_email_sent', False)}")
            print(f"  Reward: {result.get('reward', {}).get('total_reward', 0):.4f}")
            
            if result.get('details', {}).get('real_email_sent'):
                print("  ✓ Real email successfully sent!")
            else:
                print("  ℹ  Simulated email (credentials may not be configured)")
        else:
            print(f"✗ FAILED (Status: {response.status_code})")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check PRODUCTION_STATUS.txt for deployment info")
    print("2. See EMAIL_INTEGRATION.md for full configuration guide")
    print("3. Visit http://localhost:3000 to test the UI")
    print("4. To enable real email, create .env from .env.example")

if __name__ == "__main__":
    test_email_action()
