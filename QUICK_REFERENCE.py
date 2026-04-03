"""
QUICK REFERENCE GUIDE
APEXEnv - Autonomous Productivity EXecutor
"""

# ============================================================================
# IMPORTS
# ============================================================================

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
    Observation,
    Reward,
)
from apex_env.state import Contact, Task
from datetime import datetime, timedelta


# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

# Create with default config
env = APEXEnv()

# Create with custom config
config = EnvironmentConfig(
    max_episode_steps=100,
    step_delay_ms=50,
    seed=42,
    enable_logging=True,
    num_contacts=1000,
)
env = APEXEnv(config=config)

# Reset episode
obs = env.reset()

# Access state
state = env.state


# ============================================================================
# ACTIONS
# ============================================================================

# Send Email
email = EmailAction(
    recipient_id=0,                    # Contact ID
    subject="Meeting Request",         # Max 200 chars
    body="Hi Alice, are you free?",   # Max 5000 chars
    priority=PriorityEnum.HIGH,        # LOW, MEDIUM, HIGH
    language=LanguageEnum.EN,          # EN, ES, FR, DE, ZH, JA
    cc_ids=[1, 2],                    # Optional
    bcc_ids=[],                       # Optional
)

# Schedule Meeting
meeting = MeetingAction(
    title="Q2 Planning",              # Max 100 chars
    attendee_ids=[0, 1, 2],           # 1-100 attendees
    scheduled_time=datetime.utcnow() + timedelta(days=1),  # Must be future
    duration_minutes=60,              # 15-480 minutes
    meeting_type=MeetingTypeEnum.VIRTUAL,  # VIRTUAL, IN_PERSON, HYBRID
    location="Virtual",               # Optional, max 200 chars
    description="Q2 planning",        # Optional, max 1000 chars
)

# Translate Text
translation = TranslationAction(
    text="Hello world",               # Max 5000 chars
    source_language=LanguageEnum.EN,  # Source language
    target_language=LanguageEnum.ES,  # Must differ from source
)

# Recognize Gesture
gesture = GestureAction(
    gesture_code=GestureEnum.SWIPE_RIGHT,  # SWIPE_LEFT, SWIPE_RIGHT, DOUBLE_TAP, etc.
    intensity=0.85,                   # 0.0-1.0
    metadata={"duration_ms": 250},    # Optional
)

# No-op Action
noop = NoOpAction(reason="Waiting")


# ============================================================================
# STEP EXECUTION
# ============================================================================

obs, reward, terminated, truncated, info = env.step(email)

# Access observation components
print(obs.email_status.sent_count)      # Number of sent emails
print(obs.calendar_status.meeting_count) # Number of meetings
print(obs.language_context.detected_language)  # Detected language
print(obs.gesture_context.last_gesture) # Last recognized gesture
print(obs.system_state.episode_step)    # Current step number

# Access reward
print(reward.total_reward)              # [-1, 1] range
print(reward.breakdown.action_success)  # Component: action success
print(reward.breakdown.task_progress)   # Component: task progress
print(reward.episode_return)            # Cumulative reward

# Check termination
if terminated:
    print("Task completed!")
if truncated:
    print("Max steps reached!")

# Access metadata
print(info["action_result"]["success"])
print(info["action_result"]["message"])
print(info["steps_taken"])
print(info["max_steps"])


# ============================================================================
# TASK MANAGEMENT
# ============================================================================

# Create task
task = Task(
    task_id=1,
    description="Send email and schedule meeting",
    task_type="combined",
    required_actions=["email", "meeting"],
)

# Set task
env.set_task(task)

# Get progress
progress = env.state.get_task_progress(1)  # [0.0, 1.0]
print(f"Task progress: {progress:.0%}")

# Mark action complete (done automatically on success)
env.state.mark_task_action_complete(1, "email")
env.state.mark_task_action_complete(1, "meeting")

# Complete task (done automatically on termination)
env.state.complete_task(1)


# ============================================================================
# STATE INSPECTION
# ============================================================================

# Contact database
contacts = env.state.contacts              # Dict[id, Contact]
contact = env.state.get_contact(0)         # Get specific contact
print(contact.name)                        # Contact name
print(contact.email)                       # Contact email
print(contact.languages)                   # Supported languages

# Email system
emails_sent = env.state.emails_sent        # List[Email]
emails_pending = env.state.emails_pending  # List[Email]
emails_failed = env.state.emails_failed    # List[Email]

# Calendar system
meetings = env.state.meetings              # Dict[id, Meeting]
conflicts = env.state.find_meeting_conflicts(meeting)

# Task management
tasks = env.state.tasks                    # Dict[id, Task]
current_task_id = env.state.current_task_id

# Language tracking
detected_lang = env.state.detected_language
lang_confidence = env.state.language_confidence
translation_history = env.state.translation_history

# Gesture tracking
gesture_history = env.state.gesture_history  # List[GestureEnum]
last_gesture = env.state.last_gesture

# Episode metrics
action_history = env.state.action_history  # List[(step, type, success)]
error_history = env.state.error_history    # List[(step, error_msg)]
episode_reward = env.state.episode_reward
episode_step = env.state.episode_step


# ============================================================================
# ERROR HANDLING
# ============================================================================

# Errors are caught automatically
try:
    bad_email = EmailAction(
        recipient_id=9999,  # Non-existent contact
        subject="Test",
        body="Test",
    )
    obs, reward, _, _, info = env.step(bad_email)
    
    if not info["action_result"]["success"]:
        print(f"Error: {info['action_result']['message']}")
        print(f"Code: {info['action_result']['error_code']}")

except Exception as e:
    print(f"Unexpected error: {e}")

# Check error history
print(f"Total errors: {len(env.state.error_history)}")
for step, error_msg in env.state.error_history:
    print(f"  Step {step}: {error_msg}")


# ============================================================================
# MULTI-STEP EPISODE
# ============================================================================

env = APEXEnv(config=EnvironmentConfig(max_episode_steps=10))
obs = env.reset()

actions = [
    EmailAction(recipient_id=0, subject="Hi", body="Hello"),
    MeetingAction(title="Meeting", attendee_ids=[0,1],
                  scheduled_time=datetime.utcnow() + timedelta(days=1),
                  duration_minutes=30, location=None, description=None),
    TranslationAction(text="Hello", source_language=LanguageEnum.EN,
                     target_language=LanguageEnum.ES),
]

total_reward = 0.0

for action in actions:
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward.total_reward
    
    print(f"Reward: {reward.total_reward:+.3f}, Total: {total_reward:+.3f}")
    
    if terminated or truncated:
        break

print(f"Episode return: {env._episode_return:.3f}")
print(f"Steps taken: {env._steps_taken}")


# ============================================================================
# OBSERVATION SPACES
# ============================================================================

# Email status
obs.email_status.pending_count
obs.email_status.inbox_count
obs.email_status.sent_count
obs.email_status.failed_count
obs.email_status.last_sent_time
obs.email_status.last_operation_success

# Calendar status
obs.calendar_status.meeting_count
obs.calendar_status.next_meeting          # Meeting or None
obs.calendar_status.conflicts              # List[Meeting]
obs.calendar_status.available_slots        # List[TimeWindow]
obs.calendar_status.busy_hours

# Language context
obs.language_context.detected_language     # LanguageEnum
obs.language_context.confidence            # 0.0-1.0
obs.language_context.alternative_languages # List[LanguageEnum]
obs.language_context.translation_available # bool
obs.language_context.last_translation      # str or None

# Gesture context
obs.gesture_context.last_gesture           # GestureEnum or None
obs.gesture_context.recognized_gesture     # GestureEnum or None
obs.gesture_context.confidence             # 0.0-1.0
obs.gesture_context.suggested_action       # str or None
obs.gesture_context.gesture_history        # List[GestureEnum]

# System state
obs.system_state.timestamp
obs.system_state.episode_step              # int
obs.system_state.memory_usage_mb           # float
obs.system_state.error_count               # int
obs.system_state.last_error                # str or None
obs.system_state.system_healthy            # bool

# Additional info
obs.inbox                                  # List[Email] (first 10)
obs.recent_meetings                        # List[Meeting] (first 5)
obs.task_description                       # str or None


# ============================================================================
# REWARD COMPONENTS
# ============================================================================

reward.total_reward                        # [-1, 1] final reward
reward.breakdown.action_success            # Correct: +1, invalid: -1
reward.breakdown.task_progress             # [0, 1] based on % complete
reward.breakdown.efficiency_penalty        # 0 or -0.2 (repeated actions)
reward.breakdown.error_penalty             # 0 or -0.3 (failed action)
reward.breakdown.language_accuracy         # Translation quality bonus
reward.episode_return                      # Cumulative reward
reward.is_episode_complete                 # bool
reward.completion_reason                   # str or None


# ============================================================================
# ENUMS
# ============================================================================

# Languages
LanguageEnum.EN  # English
LanguageEnum.ES  # Spanish
LanguageEnum.FR  # French
LanguageEnum.DE  # German
LanguageEnum.ZH  # Chinese
LanguageEnum.JA  # Japanese

# Priorities
PriorityEnum.LOW
PriorityEnum.MEDIUM
PriorityEnum.HIGH

# Meeting Types
MeetingTypeEnum.IN_PERSON
MeetingTypeEnum.VIRTUAL
MeetingTypeEnum.HYBRID

# Gestures
GestureEnum.SWIPE_LEFT
GestureEnum.SWIPE_RIGHT
GestureEnum.DOUBLE_TAP
GestureEnum.LONG_PRESS
GestureEnum.PINCH_ZOOM
GestureEnum.VOICE_COMMAND


# ============================================================================
# COMMON PATTERNS
# ============================================================================

# Pattern 1: Single action
env = APEXEnv()
env.reset()
action = EmailAction(recipient_id=0, subject="Test", body="Body")
obs, reward, done, truncated, info = env.step(action)

# Pattern 2: Multi-step episode
env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5))
obs = env.reset()
while True:
    action = create_action()  # Your logic
    obs, reward, term, trunc, info = env.step(action)
    if term or trunc:
        break

# Pattern 3: Task completion
task = Task(task_id=1, description="...", required_actions=["email", "meeting"])
env.set_task(task)
while env.state.get_task_progress(1) < 1.0:
    action = create_action()
    obs, reward, term, trunc, info = env.step(action)
    if term:
        break

# Pattern 4: Episode statistics
total_reward = 0.0
total_steps = 0
total_errors = 0

env.reset()
while total_steps < 10:
    action = create_action()
    obs, reward, term, trunc, info = env.step(action)
    total_reward += reward.total_reward
    total_steps += 1
    total_errors = len(env.state.error_history)
    
    if term or trunc:
        break

print(f"Return: {total_reward:.3f}, Steps: {total_steps}, Errors: {total_errors}")


# ============================================================================
# VALIDATION EXAMPLES
# ============================================================================

# Valid email
email_ok = EmailAction(
    recipient_id=0,
    subject="Valid Email",
    body="This is a valid email body"
)

# Invalid email - recipient doesn't exist
try:
    email_bad = EmailAction(
        recipient_id=9999,
        subject="Test",
        body="Body"
    )
    obs, _, _, _, info = env.step(email_bad)
    # Will return success=False in info
except Exception as e:
    print(f"Validation error: {e}")

# Invalid meeting - time in past
try:
    meeting_bad = MeetingAction(
        title="Past Meeting",
        attendee_ids=[0],
        scheduled_time=datetime.utcnow() - timedelta(hours=1),  # INVALID
        duration_minutes=30,
        location=None,
        description=None,
    )
    obs, _, _, _, info = env.step(meeting_bad)
    # Will return success=False in info
except Exception as e:
    print(f"Validation error: {e}")

# Invalid translation - same source and target
try:
    translation_bad = TranslationAction(
        text="Hello",
        source_language=LanguageEnum.EN,
        target_language=LanguageEnum.EN  # INVALID - same
    )
except ValueError as e:
    print(f"Validation error: {e}")


# ============================================================================
# DEBUGGING
# ============================================================================

# Enable seed for reproducibility
env = APEXEnv(config=EnvironmentConfig(seed=42))

# Check state after each step
obs, reward, _, _, info = env.step(action)
print(f"Step {env._steps_taken}:")
print(f"  Action success: {info['action_result']['success']}")
print(f"  Reward: {reward.total_reward:.3f}")
print(f"  Error count: {len(env.state.error_history)}")
print(f"  Action history: {env.state.action_history[-1]}")

# Inspect observations
print(f"Emails: {obs.email_status.sent_count}")
print(f"Meetings: {obs.calendar_status.meeting_count}")
print(f"Language: {obs.language_context.detected_language.value}")
print(f"Errors: {obs.system_state.error_count}")

# Check errors
if env.state.error_history:
    for step, error in env.state.error_history:
        print(f"Step {step}: {error}")


print("\nQuick Reference prepared! Start building agents.")
