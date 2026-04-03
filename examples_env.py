"""
Comprehensive examples demonstrating APEXEnv usage
"""

from datetime import datetime, timedelta
from apex_env import (
    APEXEnv,
    EnvironmentConfig,
    EmailAction,
    MeetingAction,
    TranslationAction,
    GestureAction,
    NoOpAction,
    LanguageEnum,
    PriorityEnum,
    MeetingTypeEnum,
    GestureEnum,
)
from apex_env.state import Task


def example_1_basic_initialization():
    """Example 1: Initialize environment with default config"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Initialization")
    print("=" * 70)
    
    config = EnvironmentConfig(
        max_episode_steps=10,
        seed=42,
    )
    
    env = APEXEnv(config=config)
    obs = env.reset()
    
    print(f"✓ Environment initialized")
    print(f"  - Contacts loaded: {len(env.state.contacts)}")
    print(f"  - Email status: {obs.email_status.pending_count} pending")
    print(f"  - System healthy: {obs.system_state.system_healthy}")
    print()


def example_2_single_email_action():
    """Example 2: Send single email action"""
    print("=" * 70)
    print("EXAMPLE 2: Single Email Action")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    obs = env.reset()
    
    # Create email action
    action = EmailAction(
        recipient_id=0,
        subject="Meeting Request",
        body="Hi Alice, would you be available for a 30-minute sync next week?",
        priority=PriorityEnum.HIGH,
        language=LanguageEnum.EN,
    )
    
    print(f"Sending email to contact 0...")
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f"✓ Step executed:")
    print(f"  - Action success: {info['action_result']['success']}")
    print(f"  - Reward: {reward.total_reward:.3f}")
    print(f"  - Reward breakdown: {reward.breakdown.model_dump()}")
    print(f"  - Emails sent: {obs.email_status.sent_count}")
    print()


def example_3_meeting_scheduling():
    """Example 3: Schedule meeting with multiple attendees"""
    print("=" * 70)
    print("EXAMPLE 3: Meeting Scheduling")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    env.reset()
    
    # Schedule meeting
    action = MeetingAction(
        title="Q2 Planning Session",
        attendee_ids=[0, 1, 2, 3],
        scheduled_time=datetime.utcnow() + timedelta(days=7),
        duration_minutes=60,
        meeting_type=MeetingTypeEnum.VIRTUAL,
        location=None,
        description="Quarterly planning and roadmap review",
    )
    
    print(f"Scheduling meeting with 4 attendees...")
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f"✓ Meeting action executed:")
    print(f"  - Success: {info['action_result']['success']}")
    print(f"  - Message: {info['action_result']['message']}")
    print(f"  - Reward: {reward.total_reward:.3f}")
    print(f"  - Meetings scheduled: {obs.calendar_status.meeting_count}")
    if obs.calendar_status.next_meeting:
        print(f"  - Next meeting: {obs.calendar_status.next_meeting.title}")
    print()


def example_4_multilingual_translation():
    """Example 4: Handle multilingual input with translation"""
    print("=" * 70)
    print("EXAMPLE 4: Multilingual Translation")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    env.reset()
    
    # Translate text
    action = TranslationAction(
        text="Good morning, I would like to schedule a meeting to discuss the new product launch strategy.",
        source_language=LanguageEnum.EN,
        target_language=LanguageEnum.ES,
    )
    
    print(f"Processing translation EN → ES...")
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f"✓ Translation action executed:")
    print(f"  - Success: {info['action_result']['success']}")
    print(f"  - Language confidence: {obs.language_context.confidence:.3f}")
    print(f"  - Reward: {reward.total_reward:.3f}")
    print(f"  - Language history: {len(env.state.translation_history)} translations")
    print()


def example_5_gesture_input():
    """Example 5: Interpret gesture input"""
    print("=" * 70)
    print("EXAMPLE 5: Gesture Recognition")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    env.reset()
    
    # Process gesture
    action = GestureAction(
        gesture_code=GestureEnum.SWIPE_RIGHT,
        intensity=0.85,
        metadata={"source": "touchscreen", "duration_ms": 250},
    )
    
    print(f"Processing gesture: SWIPE_RIGHT (intensity={action.intensity})...")
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f"✓ Gesture action executed:")
    print(f"  - Success: {info['action_result']['success']}")
    print(f"  - Recognized: {obs.gesture_context.recognized_gesture}")
    print(f"  - Confidence: {obs.gesture_context.confidence:.3f}")
    print(f"  - Suggested action: {obs.gesture_context.suggested_action}")
    print(f"  - Reward: {reward.total_reward:.3f}")
    print(f"  - Gesture history: {env.state.gesture_history}")
    print()


def example_6_multi_step_episode():
    """Example 6: Complete multi-step episode"""
    print("=" * 70)
    print("EXAMPLE 6: Multi-Step Episode")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5, seed=42))
    obs = env.reset()
    
    print(f"Starting episode with max 5 steps...")
    
    actions = [
        ("Email", EmailAction(
            recipient_id=0,
            subject="Project Sync",
            body="Let's sync on the new project timeline",
            language=LanguageEnum.EN,
        )),
        ("Meeting", MeetingAction(
            title="Project Sync",
            attendee_ids=[0, 1],
            scheduled_time=datetime.utcnow() + timedelta(days=3),
            duration_minutes=45,
            location=None,
            description=None,
        )),
        ("Translation", TranslationAction(
            text="Please confirm your availability",
            source_language=LanguageEnum.EN,
            target_language=LanguageEnum.FR,
        )),
        ("Gesture", GestureAction(
            gesture_code=GestureEnum.DOUBLE_TAP,
            intensity=0.9,
        )),
    ]
    
    total_reward = 0.0
    
    for step_num, (action_name, action) in enumerate(actions, 1):
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward.total_reward
        
        print(f"\n  Step {step_num}: {action_name}")
        print(f"    - Reward: {reward.total_reward:+.3f}")
        print(f"    - Status: Success={info['action_result']['success']}, "
              f"Steps={info['steps_taken']}/{info['max_steps']}")
        
        if terminated or truncated:
            print(f"    - Episode ended: terminated={terminated}, truncated={truncated}")
            break
    
    print(f"\n✓ Episode completed:")
    print(f"  - Total return: {total_reward:.3f}")
    print(f"  - Steps taken: {env._steps_taken}")
    print(f"  - Emails sent: {len(env.state.emails_sent)}")
    print(f"  - Meetings scheduled: {len(env.state.meetings)}")
    print()


def example_7_task_management():
    """Example 7: Set and track task progress"""
    print("=" * 70)
    print("EXAMPLE 7: Task Management and Progress Tracking")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    obs = env.reset()
    
    # Create task
    task = Task(
        task_id=1,
        description="Schedule meeting with Alice and send confirmation email",
        task_type="combined",
        required_actions=["meeting", "email"],
    )
    
    env.set_task(task)
    
    print(f"Task set: {task.description}")
    print(f"Required actions: {task.required_actions}")
    
    # Step 1: Schedule meeting
    action1 = MeetingAction(
        title="Sync with Alice",
        attendee_ids=[0],
        scheduled_time=datetime.utcnow() + timedelta(days=1),
        duration_minutes=30,
        location=None,
        description=None,
    )
    
    obs, reward, terminated, truncated, info = env.step(action1)
    progress = env.state.get_task_progress(task.task_id)
    
    print(f"\n✓ Step 1 - Meeting scheduled")
    print(f"  - Task progress: {progress:.0%}")
    print(f"  - Reward: {reward.total_reward:+.3f}")
    
    # Step 2: Send email
    action2 = EmailAction(
        recipient_id=0,
        subject="Meeting Confirmed",
        body="Hi Alice, our meeting is confirmed for tomorrow at 2 PM. Looking forward to it!",
        language=LanguageEnum.EN,
    )
    
    obs, reward, terminated, truncated, info = env.step(action2)
    progress = env.state.get_task_progress(task.task_id)
    
    print(f"\n✓ Step 2 - Email sent")
    print(f"  - Task progress: {progress:.0%}")
    print(f"  - Reward: {reward.total_reward:+.3f}")
    
    # Manual task completion
    env.state.complete_task(task.task_id)
    
    print(f"\n✓ Task completed!")
    print(f"  - Total task return: {env._episode_return:.3f}")
    print()


def example_8_error_handling():
    """Example 8: Demonstrate error handling and validation"""
    print("=" * 70)
    print("EXAMPLE 8: Error Handling and Validation")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    env.reset()
    
    test_cases = [
        ("Invalid recipient", EmailAction(
            recipient_id=9999,
            subject="Test",
            body="Test body",
        )),
        ("Past meeting time", MeetingAction(
            title="Past Meeting",
            attendee_ids=[0],
            scheduled_time=datetime.utcnow() - timedelta(hours=1),
            duration_minutes=30,
            location=None,
            description=None,
        )),
        ("Invalid gesture intensity", lambda: GestureAction(
            gesture_code=GestureEnum.SWIPE_RIGHT,
            intensity=1.5,  # Out of bounds
        ) if False else None),  # Skip this - Pydantic catches it at creation
    ]
    
    for name, action in test_cases[:2]:  # Only test first 2
        print(f"\nTesting: {name}")
        obs, reward, terminated, truncated, info = env.step(action)
        
        print(f"  - Success: {info['action_result']['success']}")
        print(f"  - Error: {info['action_result']['message']}")
        print(f"  - Reward: {reward.total_reward:+.3f}")
    
    print(f"\n✓ Error handling demonstrated")
    print(f"  - Total errors recorded: {len(env.state.error_history)}")
    print()


def example_9_observation_structure():
    """Example 9: Inspect complete observation structure"""
    print("=" * 70)
    print("EXAMPLE 9: Complete Observation Structure")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    obs = env.reset()
    
    print(f"Observation components:")
    print(f"\n  Email Status:")
    print(f"    - Pending: {obs.email_status.pending_count}")
    print(f"    - Sent: {obs.email_status.sent_count}")
    print(f"    - Failed: {obs.email_status.failed_count}")
    print(f"    - Healthy: {obs.email_status.last_operation_success}")
    
    print(f"\n  Calendar Status:")
    print(f"    - Meetings: {obs.calendar_status.meeting_count}")
    print(f"    - Next meeting: {obs.calendar_status.next_meeting}")
    print(f"    - Available slots: {len(obs.calendar_status.available_slots)}")
    print(f"    - Busy hours: {obs.calendar_status.busy_hours}")
    
    print(f"\n  Language Context:")
    print(f"    - Detected: {obs.language_context.detected_language.value}")
    print(f"    - Confidence: {obs.language_context.confidence:.2%}")
    print(f"    - Translation available: {obs.language_context.translation_available}")
    
    print(f"\n  Gesture Context:")
    print(f"    - Last gesture: {obs.gesture_context.last_gesture}")
    print(f"    - History length: {len(obs.gesture_context.gesture_history)}")
    
    print(f"\n  System State:")
    print(f"    - Step: {obs.system_state.episode_step}")
    print(f"    - Memory MB: {obs.system_state.memory_usage_mb:.1f}")
    print(f"    - Errors: {obs.system_state.error_count}")
    print(f"    - Healthy: {obs.system_state.system_healthy}")
    
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  APEX ENVIRONMENT - COMPREHENSIVE EXAMPLES".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    examples = [
        example_1_basic_initialization,
        example_2_single_email_action,
        example_3_meeting_scheduling,
        example_4_multilingual_translation,
        example_5_gesture_input,
        example_6_multi_step_episode,
        example_7_task_management,
        example_8_error_handling,
        example_9_observation_structure,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Error in {example.__name__}: {e}")
            print()
    
    print("=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
