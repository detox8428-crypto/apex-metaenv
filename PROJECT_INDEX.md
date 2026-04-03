"""
APEX ENVIRONMENT - COMPLETE PROJECT INDEX

Master index of all files created through Phase 4.
Quick navigation to understand, use, and extend the APEXEnv system.
"""

# ============================================================================
# NAVIGATION MAP
# ============================================================================

"""
APEX ENVIRONMENT PROJECT STRUCTURE:

d:\APEX\
├── Core Implementation (Phase 3)
│   ├── apex_env/
│   │   ├── __init__.py ..................... Main exports
│   │   ├── environment.py ................. APEXEnv class (520 lines)
│   │   ├── state.py ....................... State management (180 lines)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py ................. 30+ Pydantic models (650 lines)
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── base_task.py ............... Abstract base (100 lines)
│   │   │   ├── email_task.py .............. Easy task (130 lines)
│   │   │   ├── meeting_task.py ............ Medium task (170 lines)
│   │   │   └── complex_task.py ............ Hard task (180 lines)
│   │   └── graders/
│   │       ├── __init__.py
│   │       ├── base_grader.py ............. Abstract base (60 lines)
│   │       ├── email_grader.py ............ Email evaluation (180 lines)
│   │       ├── meeting_grader.py .......... Meeting evaluation (210 lines)
│   │       └── workflow_grader.py ......... Workflow evaluation (180 lines)
│
├── Documentation & Guides
│   ├── README.md ........................... Project overview (400+ lines)
│   ├── ARCHITECTURE.md ..................... System design (300+ lines)
│   ├── PROJECT_SUMMARY.md .................. Executive summary
│   ├── PHASE_4_SUMMARY.md .................. Phase 4 overview (800+ lines)
│   ├── TASKS_AND_GRADERS_GUIDE.py ......... Comprehensive guide (650+ lines)
│   └── TASKS_GRADERS_QUICK_REFERENCE.py ... Quick lookup (400+ lines)
│
├── Examples & Demonstrations
│   ├── examples_env.py ..................... Core environment examples (400+ lines)
│   ├── examples_tasks_graders.py .......... Task/grader examples (500+ lines)
│   └── QUICK_REFERENCE.py ................. Core system quick ref (450+ lines)
│
└── Tests & Validation
    ├── test_validation.py .................. Core validation tests (300+ lines)
    ├── test_tasks_graders.py ............... Task/grader tests (600+ lines)
    └── [Future] Component tests, integration tests, e2e tests
"""


# ============================================================================
# QUICK START - WHERE TO BEGIN
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                           WHERE TO BEGIN?                                 ║
╚════════════════════════════════════════════════════════════════════════════╝


IF YOU WANT TO...                          READ THIS...
──────────────────────────────────────────────────────────────────────────

Understand the overall project:
   ✓ Start with: README.md
   ✓ Then read: PROJECT_SUMMARY.md
   ✓ For details: ARCHITECTURE.md

Understand Phase 4 (Tasks & Graders):
   ✓ Start with: PHASE_4_SUMMARY.md
   ✓ Then read: TASKS_AND_GRADERS_GUIDE.py
   ✓ For quick lookup: TASKS_GRADERS_QUICK_REFERENCE.py

See working examples:
   ✓ For core: examples_env.py
   ✓ For tasks/graders: examples_tasks_graders.py
   ✓ Run with: python examples_tasks_graders.py

Run tests:
   ✓ For core: python test_validation.py
   ✓ For tasks/graders: python test_tasks_graders.py

Use in your code:
   ✓ Import: from apex_env import APEXEnv, EnvironmentConfig
   ✓ Tasks: from apex_env.tasks import EmailTask, MeetingTask
   ✓ Graders: from apex_env.graders import EmailGrader, MeetingGrader

Extend the system:
   ✓ New task type: inherit from apex_env.tasks.BaseTask
   ✓ New grader: inherit from apex_env.graders.BaseGrader
   ✓ See examples in: apex_env/tasks/email_task.py
   ✓ See examples in: apex_env/graders/email_grader.py
"""


# ============================================================================
# COMPONENT REFERENCE
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                       COMPONENT REFERENCE                                 ║
╚════════════════════════════════════════════════════════════════════════════╝


CORE CLASSES (Phase 3):
─────────────────────

apex_env.environment.APEXEnv
    ├─ reset() → np.ndarray (observation)
    ├─ step(action) → (obs, reward, done, trunc, info)
    ├─ state() → APEXEnvState
    ├─ set_task(task) → None
    └─ Properties: action_space, observation_space, max_episode_steps, seed

apex_env.state.APEXEnvState
    ├─ email_system: EmailSystem (sent, pending, failed emails)
    ├─ calendar: Calendar (scheduled meetings)
    ├─ contacts: ContactDatabase (100+ contacts)
    ├─ task_queue: TaskQueue (current tasks)
    ├─ language_state: LanguageState (language tracking)
    └─ gesture_state: GestureState (gesture history)


TASK CLASSES (Phase 4):
──────────────────────

apex_env.tasks.BaseTask (Abstract)
    ├─ evaluate(state) → float
    ├─ is_success(state) → bool
    ├─ record_action(action_type, success)
    ├─ mark_complete()
    ├─ get_instruction() → str
    └─ get_duration() → float

apex_env.tasks.EmailTask
    ├─ __init__(recipient_id, subject, body, language)
    ├─ Success threshold: 0.75
    └─ Scoring: recipient(0.30) + subject(0.25) + body(0.25) + lang(0.10) + fmt(0.10)

apex_env.tasks.MeetingTask
    ├─ __init__(attendee_ids, target_date, time_window, duration_minutes, type, title)
    ├─ Success threshold: 0.80
    └─ Scoring: scheduled(0.20) + date(0.25) + time(0.20) + duration(0.15) + attendees(0.15) + conflicts(0.05)

apex_env.tasks.ComplexWorkflowTask
    ├─ __init__(input_text, input_language, target_language, recipient_id, meeting_attendee_ids)
    ├─ Success threshold: 0.80 + all steps
    └─ Scoring: translate(0.15) + email(0.50) + meeting(0.35) + coherence(0.05)


GRADER CLASSES (Phase 4):
───────────────────────

apex_env.graders.BaseGrader (Abstract)
    ├─ evaluate(state, task_data) → float [0.0, 1.0]
    ├─ get_detailed_feedback() → str
    ├─ get_evaluation_history() → List[dict]
    ├─ Properties: evaluation_count, determinism
    └─ Feature: Audit trail with timestamps

apex_env.graders.EmailGrader
    ├─ evaluate(state, task_data) → float
    ├─ Scoring components:
    │  ├─ Recipient match: 0.30
    │  ├─ Subject match: 0.25
    │  ├─ Body match: 0.25
    │  ├─ Language: 0.10
    │  └─ Format: 0.10
    └─ Deterministic: Always same output for same input

apex_env.graders.MeetingGrader
    ├─ evaluate(state, task_data) → float
    ├─ Scoring components:
    │  ├─ Scheduled: 0.20
    │  ├─ Date: 0.25
    │  ├─ Time: 0.20
    │  ├─ Duration: 0.15
    │  ├─ Attendees: 0.15
    │  └─ Conflicts: 0.05
    ├─ Tolerances: ±15 min time, ±1 day date
    └─ Deterministic

apex_env.graders.WorkflowGrader
    ├─ evaluate(state, task_data) → float
    ├─ Supports 1-, 2-, and 3-step workflows
    ├─ Weighs steps based on workflow length
    └─ Checks coherence between steps


DATA MODELS (Phase 2):
────────────────────

Enums:
  ├─ LanguageEnum: EN, ES, FR, DE, ZH, JA
  ├─ PriorityEnum: LOW, MEDIUM, HIGH
  ├─ MeetingTypeEnum: IN_PERSON, VIRTUAL, HYBRID
  └─ Gesture Enum: SWIPE_LEFT/RIGHT, DOUBLE_TAP, LONG_PRESS, PINCH_ZOOM, VOICE_COMMAND

Actions:
  ├─ EmailAction: recipient_id, subject, body, priority, language, cc, bcc
  ├─ MeetingAction: title, attendee_ids, scheduled_time, duration, type, location
  ├─ TranslationAction: text, source_language, target_language
  ├─ GestureAction: gesture_code, intensity, metadata
  └─ NoOpAction: reason

Observations:
  ├─ EmailObservation: recipient_id, subject, body, timestamp, status
  ├─ MeetingObservation: title, attendees, time, duration, type, status
  ├─ SystemState: current_time, task_count, email_count, meeting_count
  ├─ TaskStatus: task_id, progress, status, result
  └─ Observation: emails, meetings, task_status, system_state, timestamp
"""


# ============================================================================
# USAGE EXAMPLES BY CATEGORY
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        USAGE EXAMPLES GUIDE                               ║
╚════════════════════════════════════════════════════════════════════════════╝


EXAMPLE 1: Basic Environment Usage
───────────────────────────────────

    from apex_env import APEXEnv, EnvironmentConfig
    
    env = APEXEnv(config=EnvironmentConfig(max_episode_steps=10, seed=42))
    obs = env.reset()
    
    for step in range(10):
        action = ...  # Your agent policy
        obs, reward, done, trunc, info = env.step(action)
        if done or trunc:
            break
    
    env.close()


EXAMPLE 2: Simple Email Task
─────────────────────────────

    from apex_env import APEXEnv, EmailAction
    from apex_env.tasks import EmailTask
    from apex_env.graders import EmailGrader
    
    env = APEXEnv()
    env.reset()
    
    task = EmailTask(
        recipient_id=0,
        subject="Meeting Request",
        body="schedule a meeting",
    )
    
    action = EmailAction(
        recipient_id=0,
        subject="Meeting Request for Tomorrow",
        body="I would like to schedule a meeting tomorrow.",
    )
    
    obs, reward, done, trunc, info = env.step(action)
    
    grader = EmailGrader()
    score = grader.evaluate(env.state, {
        "expected_recipient_id": 0,
        "expected_subject": "Meeting Request",
        "expected_body": "schedule",
    })
    
    print(f"Score: {score:.2f}")
    print(grader.get_detailed_feedback())


EXAMPLE 3: Meeting Task with Constraints
──────────────────────────────────────────

    from datetime import datetime, timedelta
    from apex_env.tasks import MeetingTask
    from apex_env.graders import MeetingGrader
    
    target_date = datetime.utcnow() + timedelta(days=3)
    
    task = MeetingTask(
        attendee_ids=[0, 1, 2],
        target_date=target_date,
        time_window=(9, 17),
        duration_minutes=60,
        meeting_type=MeetingTypeEnum.VIRTUAL,
    )
    
    # Execute action...
    
    grader = MeetingGrader()
    score = grader.evaluate(env.state, {
        "expected_date": target_date,
        "expected_time_window": (9, 17),
        "expected_attendee_ids": [0, 1, 2],
        "expected_duration": 60,
        "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
    })


EXAMPLE 4: Workflow Task (Multi-Step)
──────────────────────────────────────

    from apex_env.tasks import ComplexWorkflowTask
    from apex_env.graders import WorkflowGrader
    
    task = ComplexWorkflowTask(
        input_text="Good morning. Schedule a meeting for tomorrow.",
        input_language=LanguageEnum.EN,
        target_language=LanguageEnum.ES,
        recipient_id=0,
        meeting_attendee_ids=[0, 1],
    )
    
    # Step 1: Translate
    action1 = TranslationAction(
        text="Good morning. Schedule a meeting.",
        source_language=LanguageEnum.EN,
        target_language=LanguageEnum.ES,
    )
    obs, reward, done, trunc, info = env.step(action1)
    
    # Step 2: Send email
    action2 = EmailAction(
        recipient_id=0,
        subject="Reunión",
        body="Buenos días. Quisiera programar una reunión.",
        language=LanguageEnum.ES,
    )
    obs, reward, done, trunc, info = env.step(action2)
    
    # Step 3: Schedule meeting
    action3 = MeetingAction(
        title="Reunión",
        attendee_ids=[0, 1],
        scheduled_time=...,
        duration_minutes=60,
        meeting_type=MeetingTypeEnum.VIRTUAL,
    )
    obs, reward, done, trunc, info = env.step(action3)
    
    grader = WorkflowGrader()
    score = grader.evaluate(env.state, workflow_task_data)


EXAMPLE 5: Curriculum Learning
──────────────────────────────

    from apex_env.tasks import EmailTask, MeetingTask, ComplexWorkflowTask
    
    # Create tasks with increasing difficulty
    easy_tasks = [EmailTask(...) for _ in range(10)]
    medium_tasks = [MeetingTask(...) for _ in range(10)]
    hard_tasks = [ComplexWorkflowTask(...) for _ in range(10)]
    
    # Train on each level
    for task_list in [easy_tasks, medium_tasks, hard_tasks]:
        for task in task_list:
            # Train on this task
            pass


EXAMPLE 6: Multiple Tasks Sequence
───────────────────────────────────

    tasks = [
        EmailTask(recipient_id=0, subject="Test1", body="content1"),
        MeetingTask(attendee_ids=[0], target_date=..., ...),
        EmailTask(recipient_id=1, subject="Test2", body="content2"),
    ]
    
    results = []
    for task in tasks:
        env.reset()
        action = agent.generate_action(env.reset(), task)
        obs, reward, done, trunc, info = env.step(action)
        
        grader = get_grader_for_task(task)
        score = grader.evaluate(env.state, task.get_task_data())
        
        results.append({
            'task': task.task_def.name,
            'score': score,
            'success': score >= task.success_threshold,
        })
    
    success_rate = sum(r['success'] for r in results) / len(results)
    print(f"Success rate: {success_rate:.1%}")


EXAMPLE 7: Debugging Failed Tasks
──────────────────────────────────

    task = EmailTask(...)
    action = agent_action  # Might be suboptimal
    
    obs, reward, done, trunc, info = env.step(action)
    
    grader = EmailGrader()
    score = grader.evaluate(env.state, task_data)
    
    if score < task.success_threshold:
        print(f"Task failed with score: {score:.2f}")
        print(f"Feedback: {grader.get_detailed_feedback()}")
        
        # Inspect state
        for email in env.state.email_system.sent_emails:
            print(f"Email: {email}")
"""


# ============================================================================
# EXTENDING THE SYSTEM
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                   HOW TO EXTEND THE SYSTEM                                ║
╚════════════════════════════════════════════════════════════════════════════╝


CREATE A NEW TASK TYPE:
──────────────────────

from apex_env.tasks import BaseTask
from apex_env.models import TaskDefinition

class MyCustomTask(BaseTask):
    def __init__(self, param1: str, param2: int):
        super().__init__()
        self.task_def = TaskDefinition(
            name="My Custom Task",
            description="Description of what this task does",
            difficulty="custom",  # or "easy", "medium", "hard"
        )
        self.param1 = param1
        self.param2 = param2
    
    def evaluate(self, state: APEXEnvState) -> float:
        # Implement evaluation logic
        # Return score in [0.0, 1.0]
        score = 0.0
        # ... calculate score ...
        return score
    
    def is_success(self, state: APEXEnvState) -> bool:
        score = self.evaluate(state)
        return score >= self.success_threshold  # default: 0.75


CREATE A NEW GRADER:
───────────────────

from apex_env.graders import BaseGrader

class MyCustomGrader(BaseGrader):
    def __init__(self):
        super().__init__()
        self.name = "MyCustomGrader"
    
    def evaluate(self, state: APEXEnvState, task_data: dict) -> float:
        # Implement deterministic evaluation
        score = 0.0
        
        # Score component 1
        self._record_evaluation(score, {
            'component1': ...,
            'component2': ...,
        })
        
        return score
    
    def get_detailed_feedback(self) -> str:
        # Generate human-readable feedback
        if not self.get_evaluation_history():
            return "No evaluations yet"
        
        last_eval = self.get_evaluation_history()[-1]
        feedback = f"Score: {last_eval['score']:.2f}\n"
        # ... add detailed analysis ...
        return feedback


ADD NEW ACTION TYPE:
───────────────────

from pydantic import BaseModel, Field

class MyCustomAction(BaseModel):
    param1: str = Field(..., description="Parameter 1")
    param2: int = Field(..., description="Parameter 2")
    
    class Config:
        use_enum_values = True


MODIFY GRADER PARAMETERS:
────────────────────────

# Pass custom parameters to grader
task_data = {
    'expected_recipient_id': 0,
    'expected_subject': 'Test',
    'expected_body': 'test',
    'custom_param_1': value1,
    'custom_param_2': value2,
}

score = grader.evaluate(env.state, task_data)
"""


# ============================================================================
# COMMON PATTERNS & BEST PRACTICES
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                  BEST PRACTICES & PATTERNS                                ║
╚════════════════════════════════════════════════════════════════════════════╝


PATTERN 1: Reproducible Experiments
────────────────────────────────────

    # Always use seed for reproducibility
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    os.environ['PYTHONHASHSEED'] = '0'
    np.random.seed(42)
    random.seed(42)
    
    # Graders are deterministic by default


PATTERN 2: Error Handling
─────────────────────────

    try:
        obs, reward, done, trunc, info = env.step(action)
    except ValueError as e:
        print(f"Invalid action: {e}")
    
    score = grader.evaluate(env.state, task_data)
    if score is None:
        print("Grader evaluation failed")


PATTERN 3: Logging & Metrics
─────────────────────────────

    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    grader = EmailGrader()
    
    for epoch in range(100):
        score = grader.evaluate(env.state, task_data)
        logger.info(f"Epoch {epoch}: score={score:.2f}")
    
    # Review history
    history = grader.get_evaluation_history()
    logger.info(f"Total evaluations: {len(history)}")


PATTERN 4: Validation & Testing
────────────────────────────────

    def test_grader_determinism():
        grader = EmailGrader()
        scores = []
        
        for _ in range(5):
            score = grader.evaluate(env.state, task_data)
            scores.append(score)
        
        assert all(s == scores[0] for s in scores), "Grader not deterministic!"


PATTERN 5: Task Evaluation Pipeline
────────────────────────────────────

    def evaluate_task(env, task, grader, agent_policy):
        obs = env.reset()
        
        # Get instruction
        instruction = task.get_instruction()
        
        # Generate action
        action = agent_policy(obs, instruction)
        
        # Execute
        obs, reward, done, trunc, info = env.step(action)
        
        # Evaluate
        score = grader.evaluate(env.state, task.get_task_data())
        
        # Mark complete
        task.evaluate_score = score
        task.mark_complete()
        
        return {
            'score': score,
            'success': score >= task.success_threshold,
            'duration': task.get_duration(),
            'feedback': grader.get_detailed_feedback(),
        }


BEST PRACTICES:
──────────────

1. ALWAYS use seeds for reproducibility
2. ALWAYS validate action before stepping
3. ALWAYS record metrics for analysis
4. ALWAYS use grader.get_detailed_feedback() for debugging
5. ALWAYS check score >= success_threshold for success
6. ALWAYS use try-except for robustness
7. ALWAYS log important events
8. DO NOT modify grader.evaluation_history directly
9. DO NOT assume grader scores are random
10. DO NOT skip validation steps
"""


# ============================================================================
# ARCHITECTURE DIAGRAM
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    SYSTEM ARCHITECTURE OVERVIEW                           ║
╚════════════════════════════════════════════════════════════════════════════╝

HIGH-LEVEL ARCHITECTURE:

┌─────────────────────────────────────────────────────────────────────────┐
│                          AGENT / USER CODE                              │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      TASK DEFINITION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  EmailTask   │  │ MeetingTask  │  │  Workflow    │                  │
│  │  (Easy)      │  │  (Medium)    │  │  Task (Hard) │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    APEX ENVIRONMENT LAYER                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ APEXEnv.step(action)                                            │   │
│  │  ├─ Prepare Phase                                               │   │
│  │  ├─ Validate Phase                                              │   │
│  │  ├─ Route Phase                                                 │   │
│  │  ├─ Execute Phase (action handlers)                             │   │
│  │  ├─ Reward Phase                                                │   │
│  │  ├─ Termination Phase                                           │   │
│  │  └─ Observation Phase                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  STATE: email_system, calendar, contacts, tasks, language, gesture     │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     GRADING & EVALUATION LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │EmailGrader   │  │MeetingGrader │  │WorkflowGrader│                  │
│  │              │  │              │  │              │                  │
│  │score[0,1]    │  │score[0,1]    │  │score[0,1]    │                  │
│  │deterministic │  │deterministic │  │deterministic │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         METRICS & FEEDBACK                              │
│  ├─ Score (continuous) [0.0, 1.0]                                      │
│  ├─ Success (binary) based on threshold                                 │
│  ├─ Duration (execution time)                                           │
│  ├─ Detailed Feedback (human-readable)                                  │
│  └─ Evaluation History (audit trail)                                    │
└─────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# QUICK REFERENCE - FILE LOCATIONS
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════╗
║                    FILE LOCATIONS - QUICK MAP                         ║
╚════════════════════════════════════════════════════════════════════════╝

Need to find...?                              Location
─────────────────────────────────────────────────────────────────────

Main environment class →                      apex_env/environment.py
Internal state management →                   apex_env/state.py
Data models & schemas →                       apex_env/models/schemas.py

EmailTask class →                             apex_env/tasks/email_task.py
MeetingTask class →                           apex_env/tasks/meeting_task.py
ComplexWorkflowTask class →                   apex_env/tasks/complex_task.py
BaseTask base class →                         apex_env/tasks/base_task.py

EmailGrader class →                           apex_env/graders/email_grader.py
MeetingGrader class →                         apex_env/graders/meeting_grader.py
WorkflowGrader class →                        apex_env/graders/workflow_grader.py
BaseGrader base class →                       apex_env/graders/base_grader.py

Core system examples →                        examples_env.py
Task/grader examples →                        examples_tasks_graders.py
Quick reference for core →                    QUICK_REFERENCE.py

Core system tests →                           test_validation.py
Task/grader tests →                           test_tasks_graders.py

Project overview →                            README.md
Architecture details →                        ARCHITECTURE.md
Phase 4 overview →                            PHASE_4_SUMMARY.md
Tasks/graders comprehensive guide →           TASKS_AND_GRADERS_GUIDE.py
Tasks/graders quick reference →               TASKS_GRADERS_QUICK_REFERENCE.py

This navigation guide →                       PROJECT_INDEX.md
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════╗
║                       TROUBLESHOOTING                                  ║
╚════════════════════════════════════════════════════════════════════════╝

PROBLEM                          SOLUTION
────────────────────────────────────────────────────────────────────────

ImportError when importing       Verify apex_env/ exists
APEXEnv                          Verify __init__.py files present
                                Check PYTHONPATH includes project root

Grader returns 0.0 score         Check env.step() was called first
                                 Verify action was correct type
                                 Check expected params in task_data

Task success_threshold not       Review grader feedback
met despite good score           Check threshold values:
                                   Email: >= 0.75
                                   Meeting: >= 0.80
                                   Workflow: >= 0.80

Grader scores vary between       Graders are deterministic
runs                             Issue is likely in environment
                                 Use seed: EnvironmentConfig(seed=42)

Workflow grader fails            Verify all steps executed
                                 Check step order correct
                                 Review step_data parameters

Test failures                    Run with verbose: pytest -v
                                 Review test output carefully
                                 Check example files match your code

Memory issues                    APEXEnv state grows with history
                                 Call env.reset() between episodes
                                 Consider periodic cleanup

Performance issues               Step() is fast (< 1ms)
                                 Grader.evaluate() is fast (< 1ms)
                                 Look for issues in your code

For more help:                   See TASKS_AND_GRADERS_GUIDE.py
                                 Run examples_tasks_graders.py
                                 Read docstrings in source files
"""


if __name__ == "__main__":
    print(__doc__)
    print("\n✓ Navigation guide complete")
    print("✓ Start from 'WHERE TO BEGIN' section above")
    print("✓ Choose your entry point based on what you want to do")
