"""
Example usage of APEXEnv Pydantic models
Demonstrates all model types: Actions, Observations, Rewards
"""

from datetime import datetime, timedelta
from apex_env.models import (
    # Actions
    EmailAction,
    MeetingAction,
    TranslationAction,
    GestureAction,
    NoOpAction,
    # Observations
    EmailStatus,
    CalendarStatus,
    LanguageContext,
    GestureContext,
    SystemState,
    Observation,
    Email,
    Meeting,
    TimeWindow,
    # Rewards
    RewardBreakdown,
    Reward,
    # Enums
    LanguageEnum,
    PriorityEnum,
    MeetingTypeEnum,
    GestureEnum,
    # Info
    ActionResult,
    StepInfo,
    EnvironmentConfig,
)


def example_email_action():
    """Create and validate an email action"""
    print("=" * 60)
    print("EMAIL ACTION EXAMPLE")
    print("=" * 60)
    
    email = EmailAction(
        recipient_id=42,
        subject="Meeting Confirmation",
        body="Hi Alice, I'd like to schedule a meeting next Tuesday at 2 PM.",
        priority=PriorityEnum.HIGH,
        language=LanguageEnum.EN,
        cc_ids=[10, 20],
    )
    print(email.model_dump_json(indent=2))
    print()


def example_meeting_action():
    """Create and validate a meeting action"""
    print("=" * 60)
    print("MEETING ACTION EXAMPLE")
    print("=" * 60)
    
    meeting = MeetingAction(
        title="Q2 Planning Session",
        attendee_ids=[1, 2, 3, 4, 5],
        scheduled_time=datetime.now() + timedelta(days=7),
        duration_minutes=120,
        meeting_type=MeetingTypeEnum.VIRTUAL,
        location=None,
        description="Quarterly planning and roadmap discussion",
    )
    print(meeting.model_dump_json(indent=2))
    print()


def example_translation_action():
    """Create and validate a translation action"""
    print("=" * 60)
    print("TRANSLATION ACTION EXAMPLE")
    print("=" * 60)
    
    translation = TranslationAction(
        text="Good morning, how can I assist you today?",
        source_language=LanguageEnum.EN,
        target_language=LanguageEnum.ES,
    )
    print(translation.model_dump_json(indent=2))
    print()


def example_gesture_action():
    """Create and validate a gesture action"""
    print("=" * 60)
    print("GESTURE ACTION EXAMPLE")
    print("=" * 60)
    
    gesture = GestureAction(
        gesture_code=GestureEnum.SWIPE_RIGHT,
        intensity=0.8,
        metadata={"x_start": 100, "y_start": 500, "x_end": 400, "y_end": 500},
    )
    print(gesture.model_dump_json(indent=2))
    print()


def example_observation():
    """Create a complete observation"""
    print("=" * 60)
    print("OBSERVATION EXAMPLE")
    print("=" * 60)
    
    now = datetime.utcnow()
    
    email_status = EmailStatus(
        pending_count=3,
        inbox_count=15,
        sent_count=42,
        failed_count=1,
        last_sent_time=now - timedelta(minutes=5),
        last_operation_success=True,
    )
    
    next_meeting = Meeting(
        meeting_id=1,
        title="Team Standup",
        attendee_ids=[1, 2, 3],
        scheduled_time=now + timedelta(hours=1),
        duration_minutes=30,
        meeting_type=MeetingTypeEnum.VIRTUAL,
        created_at=now,
    )
    
    calendar_status = CalendarStatus(
        meeting_count=5,
        next_meeting=next_meeting,
        conflicts=[],
        available_slots=[
            TimeWindow(
                start_time=now + timedelta(hours=2),
                end_time=now + timedelta(hours=3),
            ),
            TimeWindow(
                start_time=now + timedelta(hours=4),
                end_time=now + timedelta(hours=5),
            ),
        ],
        busy_hours=6,
    )
    
    language_context = LanguageContext(
        detected_language=LanguageEnum.EN,
        confidence=0.95,
        alternative_languages=[LanguageEnum.ES],
        translation_available=True,
    )
    
    gesture_context = GestureContext(
        last_gesture=GestureEnum.SWIPE_RIGHT,
        recognized_gesture=GestureEnum.SWIPE_RIGHT,
        confidence=0.88,
        suggested_action="Acknowledge task",
        gesture_history=[GestureEnum.SWIPE_RIGHT, GestureEnum.DOUBLE_TAP],
    )
    
    system_state = SystemState(
        timestamp=now,
        episode_step=15,
        memory_usage_mb=128.5,
        error_count=0,
        system_healthy=True,
    )
    
    observation = Observation(
        email_status=email_status,
        calendar_status=calendar_status,
        language_context=language_context,
        gesture_context=gesture_context,
        system_state=system_state,
        task_description="Schedule a meeting with Alice next Tuesday at 2 PM and send confirmation",
    )
    
    print(observation.model_dump_json(indent=2))
    print()


def example_reward():
    """Create a reward signal"""
    print("=" * 60)
    print("REWARD EXAMPLE")
    print("=" * 60)
    
    breakdown = RewardBreakdown(
        action_success=1.0,
        task_progress=0.5,
        efficiency_penalty=-0.1,
        error_penalty=0.0,
        language_accuracy=0.95,
    )
    
    reward = Reward(
        total_reward=0.85,
        breakdown=breakdown,
        episode_return=12.5,
        is_episode_complete=False,
    )
    
    print(reward.model_dump_json(indent=2))
    print()


def example_config():
    """Create environment configuration"""
    print("=" * 60)
    print("ENVIRONMENT CONFIG EXAMPLE")
    print("=" * 60)
    
    config = EnvironmentConfig(
        max_episode_steps=100,
        step_delay_ms=50,
        seed=42,
        enable_logging=True,
        language_default=LanguageEnum.EN,
        num_contacts=1000,
        num_meetings_capacity=500,
    )
    
    print(config.model_dump_json(indent=2))
    print()


def example_validation_errors():
    """Demonstrate Pydantic validation"""
    print("=" * 60)
    print("VALIDATION EXAMPLES")
    print("=" * 60)
    
    # Example 1: Invalid recipient ID
    try:
        EmailAction(
            recipient_id=15000,  # Out of bounds
            subject="Test",
            body="Test body",
        )
    except ValueError as e:
        print(f"❌ Invalid recipient ID: {e}")
    
    # Example 2: Empty subject
    try:
        EmailAction(
            recipient_id=10,
            subject="",  # Empty
            body="Test body",
        )
    except ValueError as e:
        print(f"❌ Empty subject: {e}")
    
    # Example 3: Duplicate attendees
    try:
        MeetingAction(
            title="Test Meeting",
            attendee_ids=[1, 2, 2, 3],  # Duplicate
            scheduled_time=datetime.now() + timedelta(days=1),
            duration_minutes=60,
            location=None,
            description=None,
        )
    except ValueError as e:
        print(f"❌ Duplicate attendees: {e}")
    
    # Example 4: Same source and target language
    try:
        TranslationAction(
            text="Hello",
            source_language=LanguageEnum.EN,
            target_language=LanguageEnum.EN,  # Same
        )
    except ValueError as e:
        print(f"❌ Same languages: {e}")
    
    # Example 5: Invalid gesture intensity
    try:
        GestureAction(
            gesture_code=GestureEnum.SWIPE_LEFT,
            intensity=1.5,  # Out of bounds
        )
    except ValueError as e:
        print(f"❌ Invalid intensity: {e}")
    
    print()


if __name__ == "__main__":
    example_email_action()
    example_meeting_action()
    example_translation_action()
    example_gesture_action()
    example_observation()
    example_reward()
    example_config()
    example_validation_errors()
    
    print("=" * 60)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("=" * 60)
