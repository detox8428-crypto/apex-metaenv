"""
APEX Environment - FastAPI Client

Example client showing how to use the REST API server.

Usage:
1. Start server: python server.py
2. In another terminal: python client_example.py
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class APEXClient:
    """Client for APEX Environment API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def reset(self, seed: Optional[int] = None, max_steps: int = 100) -> Dict[str, Any]:
        """Reset environment
        
        Args:
            seed: Random seed for reproducibility
            max_steps: Maximum steps per episode
            
        Returns:
            Reset response with initial observation
        """
        payload = {
            "seed": seed,
            "max_episode_steps": max_steps,
        }
        response = self.session.post(f"{self.base_url}/reset", json=payload)
        response.raise_for_status()
        return response.json()
    
    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one step
        
        Args:
            action: Action dictionary with action_type and action-specific fields
            
        Returns:
            Step response with observation, reward, done, truncated, info
        """
        payload = {"action": action}
        response = self.session.post(f"{self.base_url}/step", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state
        
        Returns:
            State response with environment state
        """
        response = self.session.get(f"{self.base_url}/state")
        response.raise_for_status()
        return response.json()
    
    def set_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set a task
        
        Args:
            task_type: Task type (email, meeting, workflow)
            task_data: Task-specific data
            
        Returns:
            Task response with task name and instruction
        """
        payload = {
            "task_type": task_type,
            "task_data": task_data,
        }
        response = self.session.post(f"{self.base_url}/task", json=payload)
        response.raise_for_status()
        return response.json()
    
    def evaluate(self, grader_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate with grader
        
        Args:
            grader_type: Grader type (email, meeting, workflow)
            task_data: Evaluation criteria
            
        Returns:
            Evaluation response with score and feedback
        """
        payload = {
            "grader_type": grader_type,
            "task_data": task_data,
        }
        response = self.session.post(f"{self.base_url}/evaluate", json=payload)
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close session"""
        self.session.close()


# ============================================================================
# EXAMPLES
# ============================================================================

def example_1_health_check():
    """Example 1: Check server health"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Health Check")
    print("=" * 70)
    
    client = APEXClient()
    
    response = client.health_check()
    print(f"Status: {response['status']}")
    print(f"Environment initialized: {response['environment_initialized']}")
    print(f"Timestamp: {response['timestamp']}")
    
    client.close()


def example_2_reset_and_get_state():
    """Example 2: Reset environment and get state"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Reset and Get State")
    print("=" * 70)
    
    client = APEXClient()
    
    # Reset with seed
    print("\n1. Resetting environment...")
    reset_response = client.reset(seed=42, max_steps=10)
    print(f"✓ Status: {reset_response['status']}")
    print(f"✓ Message: {reset_response['message']}")
    
    # Get state
    print("\n2. Getting state...")
    state_response = client.get_state()
    print(f"✓ Step count: {state_response['step_count']}")
    print(f"✓ Episode reward: {state_response['episode_reward']}")
    print(f"✓ Emails sent: {state_response['state']['email_system']['sent_count']}")
    print(f"✓ Meetings scheduled: {state_response['state']['calendar']['meeting_count']}")
    
    client.close()


def example_3_simple_email_task():
    """Example 3: Execute simple email task"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Simple Email Task")
    print("=" * 70)
    
    client = APEXClient()
    
    # Reset
    print("\n1. Resetting environment...")
    client.reset(seed=42)
    print("✓ Environment reset")
    
    # Set task
    print("\n2. Setting email task...")
    task_response = client.set_task(
        task_type="email",
        task_data={
            "recipient_id": 0,
            "subject": "Meeting Request",
            "body": "schedule a meeting",
            "language": "EN",
        }
    )
    print(f"✓ Task: {task_response['task_name']}")
    print(f"✓ Difficulty: {task_response['difficulty']}")
    print(f"✓ Instruction: {task_response['instruction']}")
    
    # Execute action
    print("\n3. Sending email...")
    step_response = client.step({
        "action_type": "email",
        "recipient_id": 0,
        "subject": "Meeting Request for Tomorrow",
        "body": "I would like to schedule a meeting tomorrow.",
        "language": "EN",
    })
    print(f"✓ Reward: {step_response['reward']}")
    print(f"✓ Done: {step_response['done']}")
    
    # Evaluate
    print("\n4. Evaluating email...")
    eval_response = client.evaluate(
        grader_type="email",
        task_data={
            "expected_recipient_id": 0,
            "expected_subject": "Meeting Request",
            "expected_body": "schedule meeting",
            "expected_language": "EN",
        }
    )
    print(f"✓ Score: {eval_response['score']:.2f}/1.00")
    print(f"✓ Success: {eval_response['success']}")
    print(f"✓ Feedback:\n{eval_response['feedback']}")
    
    client.close()


def example_4_meeting_task():
    """Example 4: Schedule meeting task"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Meeting Task")
    print("=" * 70)
    
    client = APEXClient()
    
    # Reset
    print("\n1. Resetting environment...")
    client.reset(seed=42)
    print("✓ Environment reset")
    
    # Calculate target date
    target_date = (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"
    
    # Set task
    print("\n2. Setting meeting task...")
    task_response = client.set_task(
        task_type="meeting",
        task_data={
            "attendee_ids": [0, 1, 2],
            "target_date": target_date,
            "time_window": [9, 17],
            "duration_minutes": 60,
            "meeting_type": "VIRTUAL",
            "title": "Q2 Planning",
        }
    )
    print(f"✓ Task: {task_response['task_name']}")
    print(f"✓ Instruction: {task_response['instruction']}")
    
    # Execute action
    print("\n3. Scheduling meeting...")
    meeting_time = (datetime.utcnow() + timedelta(days=3, hours=2)).isoformat() + "Z"
    step_response = client.step({
        "action_type": "meeting",
        "title": "Q2 Planning Session",
        "attendee_ids": [0, 1, 2],
        "scheduled_time": meeting_time,
        "duration_minutes": 60,
        "meeting_type": "VIRTUAL",
    })
    print(f"✓ Reward: {step_response['reward']}")
    
    # Evaluate
    print("\n4. Evaluating meeting...")
    eval_response = client.evaluate(
        grader_type="meeting",
        task_data={
            "expected_date": target_date,
            "expected_time_window": [9, 17],
            "expected_attendee_ids": [0, 1, 2],
            "expected_duration": 60,
            "expected_meeting_type": "VIRTUAL",
        }
    )
    print(f"✓ Score: {eval_response['score']:.2f}/1.00")
    print(f"✓ Success: {eval_response['success']}")
    
    client.close()


def example_5_workflow_task():
    """Example 5: Multilingual workflow task"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Multilingual Workflow Task")
    print("=" * 70)
    
    client = APEXClient()
    
    # Reset
    print("\n1. Resetting environment...")
    client.reset(seed=42)
    print("✓ Environment reset")
    
    # Set task
    print("\n2. Setting workflow task...")
    task_response = client.set_task(
        task_type="workflow",
        task_data={
            "input_text": "Good morning. Let's schedule a meeting tomorrow.",
            "input_language": "EN",
            "target_language": "ES",
            "recipient_id": 0,
            "meeting_attendee_ids": [0, 1],
        }
    )
    print(f"✓ Task: {task_response['task_name']}")
    
    # Step 1: Translate
    print("\n3. Translating...")
    client.step({
        "action_type": "translation",
        "text": "Good morning. Let's schedule a meeting.",
        "source_language": "EN",
        "target_language": "ES",
    })
    print("✓ Translation executed")
    
    # Step 2: Send email
    print("\n4. Sending email in Spanish...")
    client.step({
        "action_type": "email",
        "recipient_id": 0,
        "subject": "Reunión",
        "body": "Buenos días. Quisiera agendar una reunión mañana.",
        "language": "ES",
    })
    print("✓ Email sent")
    
    # Step 3: Schedule meeting
    print("\n5. Scheduling meeting...")
    meeting_time = (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat() + "Z"
    client.step({
        "action_type": "meeting",
        "title": "Reunión",
        "attendee_ids": [0, 1],
        "scheduled_time": meeting_time,
        "duration_minutes": 60,
        "meeting_type": "VIRTUAL",
    })
    print("✓ Meeting scheduled")
    
    # Evaluate
    print("\n6. Evaluating workflow...")
    eval_response = client.evaluate(
        grader_type="workflow",
        task_data={
            "steps": ["translate", "email", "meeting"],
            "step_1_data": {
                "source_language": "EN",
                "target_language": "ES",
            },
            "step_2_data": {
                "expected_recipient_id": 0,
                "expected_subject": "Reunión",
                "expected_body": "reunión",
                "expected_language": "ES",
            },
            "step_3_data": {
                "expected_date": meeting_time,
                "expected_attendee_ids": [0, 1],
            },
        }
    )
    print(f"✓ Score: {eval_response['score']:.2f}/1.00")
    print(f"✓ Success: {eval_response['success']}")
    
    client.close()


def example_6_multiple_steps():
    """Example 6: Multiple steps with state tracking"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Multiple Steps with State Tracking")
    print("=" * 70)
    
    client = APEXClient()
    
    # Reset
    print("\n1. Resetting environment...")
    client.reset(seed=42)
    print("✓ Environment reset")
    
    # Execute multiple steps
    actions = [
        {
            "action_type": "email",
            "recipient_id": 0,
            "subject": "Action Item 1",
            "body": "Please review the document.",
        },
        {
            "action_type": "email",
            "recipient_id": 1,
            "subject": "Action Item 2",
            "body": "Please approve the request.",
        },
        {
            "action_type": "noop",
            "reason": "Waiting for feedback",
        },
    ]
    
    total_reward = 0
    for i, action in enumerate(actions, 1):
        print(f"\n{i}. Executing action: {action['action_type']}")
        step_response = client.step(action)
        reward = step_response['reward']
        total_reward += reward
        print(f"   Reward: {reward}")
    
    # Get final state
    print("\n4. Getting final state...")
    state_response = client.get_state()
    print(f"✓ Total steps: {state_response['step_count']}")
    print(f"✓ Episode reward: {state_response['episode_reward']:.2f}")
    print(f"✓ Total emails: {state_response['state']['email_system']['sent_count']}")
    
    client.close()


def example_7_error_handling():
    """Example 7: Error handling"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Error Handling")
    print("=" * 70)
    
    client = APEXClient()
    
    try:
        print("\n1. Attempting to step without reset...")
        client.step({"action_type": "email", "recipient_id": 0})
    except requests.exceptions.HTTPError as e:
        print(f"✓ Caught error: {e.response.status_code} - {e.response.json()['detail']}")
    
    try:
        print("\n2. Resetting environment...")
        client.reset()
        print("✓ Reset successful")
        
        print("\n3. Attempting invalid action...")
        client.step({"action_type": "invalid_action"})
    except requests.exceptions.HTTPError as e:
        print(f"✓ Caught error: {e.response.status_code} - {e.response.json()['detail']}")
    
    client.close()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  APEX ENVIRONMENT - FASTAPI CLIENT EXAMPLES".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    examples = [
        example_1_health_check,
        example_2_reset_and_get_state,
        example_3_simple_email_task,
        example_4_meeting_task,
        example_5_workflow_task,
        example_6_multiple_steps,
        example_7_error_handling,
    ]
    
    print("\n⚠️  IMPORTANT: Start the server first!")
    print("   Run in a separate terminal: python server.py")
    print("\n📌 Waiting for server to be ready...\n")
    
    # Try to connect
    import time
    client = APEXClient()
    for attempt in range(10):
        try:
            client.health_check()
            print("✓ Connected to server!\n")
            break
        except requests.exceptions.ConnectionError:
            if attempt < 9:
                print(f"  Connecting... ({attempt + 1}/10)")
                time.sleep(1)
            else:
                print("✗ Could not connect to server")
                print("  Please start the server with: python server.py")
                exit(1)
    client.close()
    
    # Run examples
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\n📖 For more information:")
    print("   - Interactive docs: http://localhost:8000/docs")
    print("   - Alternative docs: http://localhost:8000/redoc")
    print("   - API info: http://localhost:8000/")
