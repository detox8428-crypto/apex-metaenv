"""
TASKS & GRADERS QUICK REFERENCE

Fast lookup guide for common tasks and graders usage.
"""

# ============================================================================
# IMPORTS
# ============================================================================

from apex_env import APEXEnv, EnvironmentConfig, EmailAction, MeetingAction, TranslationAction
from apex_env.tasks import EmailTask, MeetingTask, ComplexWorkflowTask, BaseTask
from apex_env.graders import EmailGrader, MeetingGrader, WorkflowGrader, BaseGrader
from apex_env.models import LanguageEnum, MeetingTypeEnum, PriorityEnum
from datetime import datetime, timedelta


# ============================================================================
# QUICK REFERENCE - TASKS
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                           TASK QUICK REFERENCE                            ║
╚════════════════════════════════════════════════════════════════════════════╝


TASK 1: EmailTask (Easy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIGNATURE:
    EmailTask(
        recipient_id: int,
        subject: str,
        body: str,
        language: LanguageEnum = LanguageEnum.EN,
    )

QUICK EXAMPLES:

    # Simple email
    task1 = EmailTask(
        recipient_id=0,
        subject="Meeting Request",
        body="schedule a meeting",
    )
    
    # Email in Spanish
    task2 = EmailTask(
        recipient_id=5,
        subject="Actualización de Proyecto",
        body="revisión de cambios",
        language=LanguageEnum.ES,
    )
    
    # Email with multiple keywords
    task3 = EmailTask(
        recipient_id=1,
        subject="Urgent: Action Required",
        body="please review and approve",
        language=LanguageEnum.EN,
    )

SUCCESS CRITERIA:
    - Score >= 0.75
    - Recipient must match exactly
    - Subject/body must contain key terms
    
SCORING COMPONENTS:
    - Recipient match: 0.30
    - Subject match: 0.25
    - Body match: 0.25
    - Language match: 0.10
    - Format quality: 0.10


TASK 2: MeetingTask (Medium)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIGNATURE:
    MeetingTask(
        attendee_ids: List[int],
        target_date: datetime,
        time_window: Tuple[int, int],     # (9, 17) = 9am-5pm
        duration_minutes: int,
        meeting_type: MeetingTypeEnum,
        title: str,
    )

QUICK EXAMPLES:

    # Today's meeting
    task1 = MeetingTask(
        attendee_ids=[0, 1, 2],
        target_date=datetime.utcnow(),
        time_window=(14, 15),     # 2-3 PM
        duration_minutes=60,
        meeting_type=MeetingTypeEnum.VIRTUAL,
        title="Daily Standup",
    )
    
    # Next week meeting
    next_week = datetime.utcnow() + timedelta(days=7)
    task2 = MeetingTask(
        attendee_ids=[0, 3, 5],
        target_date=next_week,
        time_window=(9, 12),      # Morning
        duration_minutes=120,
        meeting_type=MeetingTypeEnum.IN_PERSON,
        title="Sprint Planning",
    )
    
    # Evening meeting
    task3 = MeetingTask(
        attendee_ids=[1],
        target_date=datetime.utcnow() + timedelta(days=1),
        time_window=(17, 18),     # 5-6 PM
        duration_minutes=30,
        meeting_type=MeetingTypeEnum.HYBRID,
        title="One-on-One",
    )

SUCCESS CRITERIA:
    - Score >= 0.80
    - Date must match (or be adjacent)
    - Time must be in window
    - All attendees must be included
    
SCORING COMPONENTS:
    - Scheduled: 0.20
    - Date match: 0.25
    - Time match: 0.20
    - Duration: 0.15
    - Attendees: 0.15
    - No conflicts: 0.05


TASK 3: ComplexWorkflowTask (Hard)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIGNATURE:
    ComplexWorkflowTask(
        input_text: str,
        input_language: LanguageEnum,
        target_language: LanguageEnum,
        recipient_id: int,
        meeting_attendee_ids: List[int],
    )

QUICK EXAMPLES:

    # English to Spanish workflow
    task1 = ComplexWorkflowTask(
        input_text="Good morning, let's schedule a meeting tomorrow.",
        input_language=LanguageEnum.EN,
        target_language=LanguageEnum.ES,
        recipient_id=0,
        meeting_attendee_ids=[0, 1, 2],
    )
    
    # French to German workflow
    task2 = ComplexWorkflowTask(
        input_text="Bonjour, je voudrais programmer une réunion.",
        input_language=LanguageEnum.FR,
        target_language=LanguageEnum.DE,
        recipient_id=3,
        meeting_attendee_ids=[3, 4],
    )

WORKFLOW STEPS:
    1. Translate input to target language
    2. Send email in target language to recipient
    3. Schedule meeting in target language
    
SUCCESS CRITERIA:
    - Score >= 0.80
    - All 3 steps must attempt completion
    - Translation must change language
    - Email in different language from input
    
SCORING COMPONENTS:
    - Translation: 0.15
    - Email: 0.50
    - Meeting: 0.35
    - Coherence: 0.05


COMMON TASK PATTERNS
━━━━━━━━━━━━━━━━━━━

PATTERN 1: Quick email validation
    task = EmailTask(
        recipient_id=0,
        subject="Important",
        body="action required",
    )
    instr = task.get_instruction()


PATTERN 2: Batch task creation
    recipients = [0, 1, 2, 3]
    tasks = [
        EmailTask(recipient_id=r, subject="Test", body="content")
        for r in recipients
    ]


PATTERN 3: Task with success tracking
    task = EmailTask(recipient_id=0, subject="Test", body="test")
    # ... execute ...
    task.evaluate_score = 0.95
    task.mark_complete()
    duration = task.get_duration()
"""


# ============================================================================
# QUICK REFERENCE - GRADERS
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                          GRADER QUICK REFERENCE                           ║
╚════════════════════════════════════════════════════════════════════════════╝


GRADER 1: EmailGrader
━━━━━━━━━━━━━━━━━━━━━

USAGE:
    grader = EmailGrader()
    score = grader.evaluate(env.state, task_data)
    feedback = grader.get_detailed_feedback()

QUICK EXAMPLES:

    # Basic email evaluation
    grader = EmailGrader()
    task_data = {
        "expected_recipient_id": 0,
        "expected_subject": "Meeting",
        "expected_body": "schedule",
        "expected_language": LanguageEnum.EN,
    }
    score = grader.evaluate(env.state, task_data)
    print(f"Score: {score:.2f}/1.00")
    
    # Email with keywords
    grader = EmailGrader()
    task_data = {
        "expected_recipient_id": 0,
        "expected_subject": "Project Status",
        "expected_body": "update",
        "expected_language": LanguageEnum.EN,
        "subject_keywords": ["project", "status"],
        "body_keywords": ["update", "progress", "complete"],
    }
    score = grader.evaluate(env.state, task_data)
    
    # Multilingual email
    grader = EmailGrader()
    task_data = {
        "expected_recipient_id": 5,
        "expected_subject": "Reunión",
        "expected_body": "mañana",
        "expected_language": LanguageEnum.ES,
    }
    score = grader.evaluate(env.state, task_data)

PARAMETERS:
    expected_recipient_id (int): Recipient ID
    expected_subject (str): Subject keywords/content
    expected_body (str): Body keywords/content
    expected_language (LanguageEnum): Email language
    subject_keywords (List[str], optional): Keywords to find in subject
    body_keywords (List[str], optional): Keywords to find in body

RETURNS:
    float: Score in [0.0, 1.0]


GRADER 2: MeetingGrader
━━━━━━━━━━━━━━━━━━━━━━

USAGE:
    grader = MeetingGrader()
    score = grader.evaluate(env.state, task_data)
    feedback = grader.get_detailed_feedback()

QUICK EXAMPLES:

    # Basic meeting evaluation
    target_date = datetime.utcnow() + timedelta(days=1)
    grader = MeetingGrader()
    task_data = {
        "expected_date": target_date,
        "expected_time_window": (9, 17),
        "expected_attendee_ids": [0, 1],
        "expected_duration": 60,
    }
    score = grader.evaluate(env.state, task_data)
    
    # Meeting with type constraint
    grader = MeetingGrader()
    task_data = {
        "expected_date": target_date,
        "expected_time_window": (14, 15),
        "expected_attendee_ids": [0, 1, 2],
        "expected_duration": 60,
        "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
        "tolerance_minutes": 15,
    }
    score = grader.evaluate(env.state, task_data)
    
    # Meeting in afternoon
    grader = MeetingGrader()
    task_data = {
        "expected_date": target_date,
        "expected_time_window": (13, 17),
        "expected_attendee_ids": [0],
        "expected_duration": 90,
        "tolerance_minutes": 30,
    }
    score = grader.evaluate(env.state, task_data)

PARAMETERS:
    expected_date (datetime): Target date
    expected_time_window (Tuple[int, int]): (hour_start, hour_end)
    expected_attendee_ids (List[int]): Required attendees
    expected_duration (int): Meeting duration in minutes
    expected_meeting_type (MeetingTypeEnum, optional): Type of meeting
    tolerance_minutes (int, optional): Time variance tolerance (default: 15)

RETURNS:
    float: Score in [0.0, 1.0]


GRADER 3: WorkflowGrader
━━━━━━━━━━━━━━━━━━━━━━━

USAGE:
    grader = WorkflowGrader()
    score = grader.evaluate(env.state, task_data)
    feedback = grader.get_detailed_feedback()

QUICK EXAMPLES:

    # 3-step workflow (translate + email + meeting)
    grader = WorkflowGrader()
    target_date = datetime.utcnow() + timedelta(days=1)
    
    task_data = {
        "steps": ["translate", "email", "meeting"],
        "step_1_data": {
            "source_language": LanguageEnum.EN,
            "target_language": LanguageEnum.ES,
        },
        "step_2_data": {
            "expected_recipient_id": 0,
            "expected_subject": "Reunión",
            "expected_body": "mañana",
            "expected_language": LanguageEnum.ES,
        },
        "step_3_data": {
            "expected_date": target_date,
            "expected_attendee_ids": [0, 1],
            "expected_duration": 60,
        },
    }
    score = grader.evaluate(env.state, task_data)
    
    # 2-step workflow (email + meeting)
    grader = WorkflowGrader()
    task_data = {
        "steps": ["email", "meeting"],
        "step_1_data": {
            "expected_recipient_id": 0,
            "expected_subject": "Meeting",
            "expected_body": "schedule",
        },
        "step_2_data": {
            "expected_date": target_date,
            "expected_attendee_ids": [0],
        },
    }
    score = grader.evaluate(env.state, task_data)

PARAMETERS:
    steps (List[str]): Workflow steps (e.g., ["translate", "email", "meeting"])
    step_N_data (dict): Evaluation data for each step
    
RETURNS:
    float: Score in [0.0, 1.0]


COMMON GRADER PATTERNS
━━━━━━━━━━━━━━━━━━━━

PATTERN 1: Simple evaluation
    score = grader.evaluate(env.state, minimal_task_data)
    if score >= 0.75:
        print("Task success!")

PATTERN 2: Detailed feedback
    score = grader.evaluate(env.state, task_data)
    feedback = grader.get_detailed_feedback()
    print(feedback)

PATTERN 3: History tracking
    history = grader.get_evaluation_history()
    for eval in history:
        print(f"Score: {eval['score']:.2f}")

PATTERN 4: Determinism verification
    grader = EmailGrader()
    scores = []
    for _ in range(3):
        score = grader.evaluate(env.state, task_data)
        scores.append(score)
    assert scores[0] == scores[1] == scores[2]  # Always true
"""


# ============================================================================
# COMPLETE WORKFLOW EXAMPLE
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                      COMPLETE WORKFLOW EXAMPLE                            ║
╚════════════════════════════════════════════════════════════════════════════╝


STEP-BY-STEP EXECUTION:
━━━━━━━━━━━━━━━━━━━━━

1. SETUP ENVIRONMENT
   ──────────────────
   env = APEXEnv(config=EnvironmentConfig(max_episode_steps=10))
   obs = env.reset()


2. CREATE TASK
   ────────────
   task = EmailTask(
       recipient_id=0,
       subject="Project Update",
       body="schedule meeting",
   )
   print(task.get_instruction())


3. AGENT GENERATES ACTION
   ──────────────────────
   action = EmailAction(
       recipient_id=0,
       subject="Project Update - Action Items",
       body="We should schedule a meeting soon.",
       language=LanguageEnum.EN,
   )


4. EXECUTE IN ENVIRONMENT
   ──────────────────────
   obs, reward, done, truncated, info = env.step(action)
   # Environment state updated with email


5. EVALUATE WITH GRADER
   ────────────────────
   grader = EmailGrader()
   task_data = {
       "expected_recipient_id": 0,
       "expected_subject": "Project Update",
       "expected_body": "schedule meeting",
       "expected_language": LanguageEnum.EN,
   }
   score = grader.evaluate(env.state, task_data)
   # Returns: 0.85 (good match)


6. DETERMINE SUCCESS
   ─────────────────
   success = score >= task.success_threshold  # 0.75
   # Result: True


7. LOG RESULTS
   ───────────
   task.evaluate_score = score
   task.mark_complete()
   
   results = {
       'task': task.task_def.name,
       'score': score,
       'success': success,
       'duration': task.get_duration(),
   }


EXPECTED OUTPUT:
════════════════

Task: Send an email to contact 0 about 'Project Update' with mention of 'schedule meeting'

Email sent:
  Recipient: 0
  Subject: Project Update - Action Items
  Body: We should schedule a meeting soon.

Grader Evaluation:
  Score: 0.85/1.00
  
  Recipient match: 0.30/0.30 ✓
  Subject match: 0.225/0.25 (substring)
  Body match: 0.20/0.25 (keyword found)
  Language match: 0.10/0.10 ✓
  Format quality: 0.10/0.10 ✓
  ─────────────────────────
  Total: 0.85/1.00

Task success: True (score >= 0.75 threshold)
Task duration: 0.23 seconds
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        TROUBLESHOOTING GUIDE                              ║
╚════════════════════════════════════════════════════════════════════════════╝


ISSUE 1: Email grader returns 0.0 score
─────────────────────────────────────────
CAUSE: No emails have been sent in the state
SOLUTION: 
    - Verify environment.step() was called with EmailAction
    - Check that action.recipient_id matches expected_recipient_id
    - Ensure env.reset() was called before executing actions


ISSUE 2: Meeting grader returns low score despite correct meeting
───────────────────────────────────────────────────────────────
CAUSE: Date/time constraints not met
SOLUTION:
    - Verify meeting date matches expected_date exactly
    - Check time window: meeting time must be in [hour_start, hour_end)
    - Verify all expected attendees are included
    - Check duration is within tolerance


ISSUE 3: Grader score varies between runs
──────────────────────────────────────────
CAUSE: Non-deterministic behavior (shouldn't happen with graders)
SOLUTION:
    - Graders are deterministic; check environment randomness
    - Use fixed seed: EnvironmentConfig(seed=42)
    - Verify grader receives same state and task_data
    - Check for timestamp-based scoring (not in current impl.)


ISSUE 4: Workflow grader not finding translated text
───────────────────────────────────────────────────────
CAUSE: TranslationAction not recorded in state
SOLUTION:
    - Verify TranslationAction was executed with env.step()
    - Check source_language and target_language match expectations
    - Ensure translation occurred BEFORE email action


ISSUE 5: Task success_threshold not met despite good score
───────────────────────────────────────────────────────────
CAUSE: Score below threshold
SOLUTION:
    - Email task: >= 0.75
    - Meeting task: >= 0.80
    - Workflow task: >= 0.80 with all steps attempted
    - Review grader feedback: print(grader.get_detailed_feedback())
"""


# ============================================================================
# COMMON PARAMETERS REFERENCE
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                     PARAMETERS QUICK LOOKUP                               ║
╚════════════════════════════════════════════════════════════════════════════╝

LANGUAGE ENUM VALUES:
    LanguageEnum.EN  - English
    LanguageEnum.ES  - Spanish
    LanguageEnum.FR  - French
    LanguageEnum.DE  - German
    LanguageEnum.ZH  - Mandarin Chinese
    LanguageEnum.JA  - Japanese

MEETING TYPE VALUES:
    MeetingTypeEnum.IN_PERSON  - Conference room
    MeetingTypeEnum.VIRTUAL    - Video call
    MeetingTypeEnum.HYBRID     - Both options

TIME WINDOW EXAMPLES:
    (9, 17)    - 9 AM to 5 PM (business hours)
    (14, 15)   - 2 PM to 3 PM (specific hour)
    (0, 24)    - Any time (24-hour span)
    (18, 20)   - 6 PM to 8 PM (evening)

COMMON GRADER TASK_DATA:

    Email task_data:
    {
        "expected_recipient_id": int,
        "expected_subject": str,
        "expected_body": str,
        "expected_language": LanguageEnum,
        "subject_keywords": [str, ...],  # optional
        "body_keywords": [str, ...],     # optional
    }
    
    Meeting task_data:
    {
        "expected_date": datetime,
        "expected_time_window": (int, int),
        "expected_attendee_ids": [int, ...],
        "expected_duration": int,  # minutes
        "expected_meeting_type": MeetingTypeEnum,  # optional
        "tolerance_minutes": int,  # default: 15
    }
    
    Workflow task_data:
    {
        "steps": ["translate", "email", "meeting"],
        "step_1_data": { ... },
        "step_2_data": { ... },
        "step_3_data": { ... },
    }
"""


if __name__ == "__main__":
    print(__doc__)
