"""
TASKS AND GRADERS - COMPREHENSIVE GUIDE

This document provides complete guidance on the APEXEnv task and grading system.

Topics:
1. Architecture Overview
2. Task Types and Difficulty Levels
3. Grader Design and Scoring
4. Integration with APEXEnv
5. Usage Patterns and Best Practices
"""

# ============================================================================
# 1. ARCHITECTURE OVERVIEW
# ============================================================================

"""
The task and grader system provides a framework for:

1. TASKS: Define what the agent should do
   - Deterministic instructions
   - Clear success/failure criteria
   - Difficulty levels (Easy, Medium, Hard)
   - Performance metrics

2. GRADERS: Evaluate how well the agent completed the task
   - Deterministic scoring (same input → same score)
   - Detailed feedback generation
   - Component-wise analysis
   - Audit trails for debugging

3. INTEGRATION: Seamless connection to APEXEnv
   - Tasks define the goal
   - Agent performs actions in environment
   - Grader evaluates final state
   - Reward signal incorporates grader score


WORKFLOW:
┌──────────────────────────────────────────────────────────────┐
│ 1. Task Definition                                           │
│    - What: Send email to recipient with subject             │
│    - Success: Score >= 0.75                                 │
│    - Difficulty: Easy                                        │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. Agent Execution (in APEXEnv)                             │
│    - obs, reward, done, trunc, info = env.step(action)      │
│    - Action: EmailAction(recipient=0, subject="...", ...)   │
│    - Updates internal state                                 │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. Grader Evaluation                                         │
│    - score = grader.evaluate(env.state, task_data)          │
│    - Analyzes state after action                            │
│    - Returns score [0.0, 1.0]                               │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. Task Success Determination                               │
│    - is_success = score >= task.success_threshold            │
│    - Task marked complete                                   │
│    - Metrics recorded                                        │
└──────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# 2. TASK TYPES AND DIFFICULTY LEVELS
# ============================================================================

"""
THREE DIFFICULTY LEVELS:


A. EASY - EmailTask (Single Step)
   └─────────────────────────────────────────────────────────

   PURPOSE: Send email matching requirements
   
   REQUIREMENTS:
   - Recipient ID: Who should receive
   - Subject: Required keywords/content
   - Body: Required keywords/content
   - Language: Correct language (default: EN)
   
   SUCCESS CRITERIA:
   - Recipient: Exact match (hard constraint)
   - Subject: Fuzzy match (substring, keyword match)
   - Body: Fuzzy match (substring, keyword match)
   - Language: Exact match
   - Overall: Score >= 0.75
   
   SCORING:
   - 0.25: Correct recipient
   - +0.25: Subject match
   - +0.25: Body match
   - +0.15: Language match
   - +0.10: Professional format
   ───────
     1.00 total
   
   EXAMPLE TASK:
   
   from apex_env.tasks import EmailTask
   from apex_env.models import LanguageEnum
   
   task = EmailTask(
       recipient_id=0,           # Send to contact #0
       subject="Project Status",  # Required in subject
       body="schedule meeting",   # Required in body
       language=LanguageEnum.EN,  # English email
   )
   
   instruction = task.get_instruction()
   # → "Send an email to contact 0 with subject about 'Project Status'..."


B. MEDIUM - MeetingTask (Single Step with Constraints)
   └─────────────────────────────────────────────────────────

   PURPOSE: Schedule meeting with constraints
   
   CONSTRAINTS:
   - Date: Specific date or date range
   - Time Window: (hour_start, hour_end) e.g., (9, 17) = 9am-5pm
   - Attendees: List of required attendee IDs
   - Duration: Meeting length in minutes (with tolerance)
   - Type: IN_PERSON, VIRTUAL, or HYBRID
   
   SCORING:
   - 0.20: Meeting scheduled (binary)
   - +0.25: Correct date (exact or adjacent)
   - +0.20: Time within window
   - +0.15: Duration matches (±15 min tolerance)
   - +0.15: All attendees included
   - +0.05: No calendar conflicts
   ───────
     1.00 total
   
   SUCCESS CRITERIA: Score >= 0.80
   
   EXAMPLE TASK:
   
   from apex_env.tasks import MeetingTask
   from datetime import datetime, timedelta
   
   target_date = datetime.utcnow() + timedelta(days=3)
   task = MeetingTask(
       attendee_ids=[0, 1, 2],
       target_date=target_date,
       time_window=(9, 17),      # 9 AM - 5 PM
       duration_minutes=60,
       meeting_type=MeetingTypeEnum.VIRTUAL,
       title="Q2 Planning",
   )
   
   instruction = task.get_instruction()
   # → "Schedule a meeting with attendees 0,1,2 for Jan 15..."


C. HARD - ComplexWorkflowTask (Multi-Step)
   └─────────────────────────────────────────────────────────

   PURPOSE: Execute multi-step workflow
            (Translate → Send Email → Schedule Meeting)
   
   WORKFLOW:
   
   Step 1: Interpret input (language/gesture)
           Action: TranslationAction
           Check: Source/target languages matched
    
   Step 2: Compose and send email
           Action: EmailAction
           Check: Subject/body in target language
           Recipient: From task requirements
    
   Step 3: Schedule follow-up meeting
           Action: MeetingAction
           Check: Meeting with recipients
           Time: Based on translated content
   
   SCORING:
   - 0.15: Translation to target language (step 1)
   - +0.50: Email to correct recipient (step 2)
   - +0.35: Meeting scheduled with attendees (step 3)
   - +0.05: Coherence (coherent action sequence)
   ───────
     1.05 (5% coherence bonus)
   
   SUCCESS CRITERIA: Score >= 0.80 + all 3 steps attempted
   
   EXAMPLE TASK:
   
   from apex_env.tasks import ComplexWorkflowTask
   
   task = ComplexWorkflowTask(
       input_text="Good morning. Let's schedule a meeting.",
       input_language=LanguageEnum.EN,
       target_language=LanguageEnum.ES,
       recipient_id=0,
       meeting_attendee_ids=[0, 1],
   )
   
   instruction = task.get_instruction()
   # → "Process multilingual input: 'Good morning...' (EN)"
   #   "Translate to Spanish (ES)"
   #   "Send email to contact 0 in Spanish"
   #   "Schedule meeting with contacts 0,1"
"""

# ============================================================================
# 3. GRADER DESIGN AND SCORING
# ============================================================================

"""
FOUR GRADER TYPES:


A. BaseGrader - Abstract Base Class
   ──────────────────────────────────

   All graders inherit from BaseGrader.
   
   KEY METHODS:
   - evaluate(state, task_data) → float [0.0, 1.0]
     * Computes score based on state and requirements
     * DETERMINISTIC: Same input always yields same output
     * No randomness or non-deterministic behavior
   
   - get_detailed_feedback() → str
     * Human-readable explanation of scoring
     * Breaks down component scores
     * Suggests improvements
   
   - get_evaluation_history() → List[dict]
     * Records all evaluations
     * Timestamped entries
     * Useful for debugging and analysis
   
   PROPERTIES:
   - evaluation_count: Number of evaluations performed
   - determinism: Guaranteed (no randomness)


B. EmailGrader - Email Evaluation
   ────────────────────────────────

   EVALUATION COMPONENTS:
   
   1. Recipient Score (0.30 total)
      └─ Checks: recipient_id matches expected
      └─ Value: 0.30 if exact match, 0.0 otherwise
   
   2. Subject Score (0.25 total)
      └─ Matching Hierarchy:
         • Exact match: 1.00 × 0.25 = 0.25
         • Substring: 0.90 × 0.25 = 0.225
         • Keyword match: 0.5-1.0 × 0.25
         • Partial word: 0.0-0.5 × 0.25
   
   3. Body Score (0.25 total)
      └─ Same matching hierarchy as subject
      └─ Content relevance evaluated
   
   4. Language Score (0.10 total)
      └─ Checks: email_language matches expected
      └─ Value: 0.10 if match, 0.0 otherwise
   
   5. Format Score (0.10 total)
      └─ Checks: Professional formatting
      └─ Length constraints (subject < 100, body < 1000)
      └─ Proper structure
   
   DETERMINISM:
   - No randomness in text matching
   - Consistent keyword scoring
   - Reproducible across runs
   
   USAGE:
   
   from apex_env.graders import EmailGrader
   
   grader = EmailGrader()
   
   task_data = {
       "expected_recipient_id": 0,
       "expected_subject": "Project Status",
       "expected_body": "update",
       "expected_language": LanguageEnum.EN,
       "subject_keywords": ["project", "status"],
       "body_keywords": ["update", "progress"],
   }
   
   score = grader.evaluate(env.state, task_data)
   print(grader.get_detailed_feedback())


C. MeetingGrader - Meeting Evaluation
   ──────────────────────────────────

   EVALUATION COMPONENTS:
   
   1. Meeting Scheduled (0.20 total)
      └─ Binary: 0.20 if meeting exists, 0.0 otherwise
   
   2. Date Score (0.25 total)
      └─ Exact match: 0.25
      └─ Adjacent day: 0.12 (50%)
      └─ Off by 2+ days: 0.0
   
   3. Time Score (0.20 total)
      └─ Exact fit in window: 0.20
      └─ Partial fit: 0.15
      └─ Off by 1 hour: 0.10
      └─ Outside window: 0.0
   
   4. Duration Score (0.15 total)
      └─ Within tolerance (±15 min default): 0.15
      └─ Off by 15-30 min: 0.10
      └─ Off by 30+ min: 0.0
   
   5. Attendee Score (0.15 total)
      └─ All required: 0.15
      └─ Partial (N-1): 0.10
      └─ Missing key attendees: 0.0
   
   6. Conflict Score (0.05 total)
      └─ No conflicts: 0.05
      └─ Conflicts detected: 0.0
   
   TOLERANCES:
   - time_tolerance: ±15 minutes (default, configurable)
   - date_tolerance: ±1 day (adjacent dates allowed)
   - duration_variance: ±15 minutes
   
   USAGE:
   
   from apex_env.graders import MeetingGrader
   
   grader = MeetingGrader()
   
   target_date = datetime.utcnow() + timedelta(days=3)
   task_data = {
       "expected_date": target_date,
       "expected_time_window": (9, 17),
       "expected_attendee_ids": [0, 1, 2],
       "expected_duration": 60,
       "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
       "tolerance_minutes": 15,
   }
   
   score = grader.evaluate(env.state, task_data)
   print(grader.get_detailed_feedback())


D. WorkflowGrader - Multi-Step Evaluation
   ──────────────────────────────────────

   PURPOSE: Evaluate complex workflows involving multiple actions
   
   WORKFLOW TYPES:
   
   Type 1: 1-Step Workflow (Single Action)
           Score = 100% × step_score
   
   Type 2: 2-Step Workflow (Email + Meeting)
           Score = 40% × email_score + 60% × meeting_score
   
   Type 3: 3+ Step Workflow (Translate + Email + Meeting)
           Score = 25% × translate_score + 
                   35% × email_score + 
                   25% × meeting_score +
                   15% × coherence_score
   
   COHERENCE VALIDATION:
   - Temporal ordering: Translate before email ✓
   - Action appropriateness: Email exists, meeting exists ✓
   - Content coherence: Email themes match meeting ✓
   - Language consistency: Translations maintain language ✓
   
   COMPOSITION:
   - Uses EmailGrader for email evaluation
   - Uses MeetingGrader for meeting evaluation
   - Adds coherence bonus if steps follow logically
   
   USAGE:
   
   from apex_env.graders import WorkflowGrader
   
   grader = WorkflowGrader()
   
   task_data = {
       "steps": ["translate", "email", "meeting"],
       "step_1_data": {
           "source_language": LanguageEnum.EN,
           "target_language": LanguageEnum.ES,
       },
       "step_2_data": {
           "expected_recipient_id": 0,
           "expected_subject": "Reunion",
           "expected_body": "meeting",
           "expected_language": LanguageEnum.ES,
       },
       "step_3_data": {
           "expected_date": target_date,
           "expected_attendee_ids": [0, 1],
       },
   }
   
   score = grader.evaluate(env.state, task_data)
   print(grader.get_detailed_feedback())
"""

# ============================================================================
# 4. INTEGRATION WITH APEXEnv
# ============================================================================

"""
COMPLETE INTEGRATION EXAMPLE:

from apex_env import APEXEnv, EnvironmentConfig, EmailAction
from apex_env.tasks import EmailTask
from apex_env.graders import EmailGrader
from apex_env.models import LanguageEnum

# 1. Create environment
env = APEXEnv(config=EnvironmentConfig(max_episode_steps=10))
obs = env.reset()

# 2. Define task
task = EmailTask(
    recipient_id=0,
    subject="Project Update",
    body="schedule meeting",
    language=LanguageEnum.EN,
)
print(f"Task: {task.get_instruction()}")

# 3. Agent acts
action = EmailAction(
    recipient_id=0,
    subject="Project Update - Action Items",
    body="Please schedule a meeting to discuss pending items.",
    language=LanguageEnum.EN,
)

obs, reward, done, truncated, info = env.step(action)
print(f"✓ Email sent")
print(f"  Reward from step: {reward}")

# 4. Evaluate with grader
grader = EmailGrader()

task_data = {
    "expected_recipient_id": 0,
    "expected_subject": "Project Update",
    "expected_body": "schedule meeting",
    "expected_language": LanguageEnum.EN,
    "subject_keywords": ["project", "update"],
    "body_keywords": ["schedule", "meeting"],
}

score = grader.evaluate(env.state, task_data)
print(f"✓ Grader score: {score:.2f}")
print(grader.get_detailed_feedback())

# 5. Task result
task.evaluate_score = score
task.mark_complete()
success = score >= task.success_threshold
print(f"✓ Task success: {success}")

# 6. Metrics
print(f"Task duration: {task.get_duration():.2f}s")
print(f"Environment steps taken: {info['step_count']}")
print(f"Episode reward: {sum of all steps}")
"""

# ============================================================================
# 5. USAGE PATTERNS AND BEST PRACTICES
# ============================================================================

"""
PATTERN 1: Sequential Task Execution
────────────────────────────────────

# Execute multiple tasks and track success rate

from apex_env.tasks import EmailTask, MeetingTask
from apex_env.graders import EmailGrader, MeetingGrader

tasks = [
    EmailTask(recipient_id=0, subject="Meeting", body="schedule"),
    MeetingTask(attendee_ids=[0, 1], target_date=..., ...),
    EmailTask(recipient_id=1, subject="Status", body="update"),
]

graders = [EmailGrader(), MeetingGrader(), EmailGrader()]

results = []
for task, grader in zip(tasks, graders):
    env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5))
    obs = env.reset()
    
    # Agent generates action (your policy here)
    action = agent.generate_action(obs, task)
    
    obs, reward, done, truncated, info = env.step(action)
    
    score = grader.evaluate(env.state, task.get_task_data())
    success = score >= task.success_threshold
    
    results.append({
        'task': task.task_def.name,
        'score': score,
        'success': success,
    })

# Calculate success rate
success_rate = sum(r['success'] for r in results) / len(results)
print(f"Success rate: {success_rate:.1%}")


PATTERN 2: Curriculum Learning
──────────────────────────────

# Train on tasks of increasing difficulty

from apex_env.tasks import EmailTask, MeetingTask, ComplexWorkflowTask

curriculum = [
    ("easy", [EmailTask(...) for _ in range(10)]),
    ("medium", [MeetingTask(...) for _ in range(10)]),
    ("hard", [ComplexWorkflowTask(...) for _ in range(10)]),
]

for phase_name, phase_tasks in curriculum:
    print(f"Training on {phase_name} tasks...")
    
    for task in phase_tasks:
        env = APEXEnv(config=EnvironmentConfig(max_episode_steps=10))
        obs = env.reset()
        
        grader = get_grader_for_task(task)
        
        # Train agent on this task
        for episode in range(100):
            action = agent.generate_action(obs, task)
            obs, reward, done, truncated, info = env.step(action)
            
            # Get grader score to supplement reward signal
            task_score = grader.evaluate(env.state, task.get_task_data())
            
            # Use combined reward for training
            combined_reward = reward + 0.5 * task_score
            agent.train_step(combined_reward)


PATTERN 3: Debugging Failed Tasks
─────────────────────────────────

# Use grader feedback to understand failures

env = APEXEnv(config=EnvironmentConfig(seed=42))
obs = env.reset()

task = EmailTask(...)
grader = EmailGrader()

# Agent action
action = agent.generate_action(obs, task)
obs, reward, done, truncated, info = env.step(action)

# Evaluate
score = grader.evaluate(env.state, task.get_task_data())
feedback = grader.get_detailed_feedback()

if score < task.success_threshold:
    print("TASK FAILED:")
    print(feedback)
    print()
    
    # Inspect state
    print("Email state:")
    for email in env.state.email_system.sent_emails:
        print(f"  To: {email.recipient_id}")
        print(f"  Subject: {email.subject}")
        print(f"  Body: {email.body}")


PATTERN 4: Grader History and Logging
────────────────────────────────────

# Audit trail for reproducibility

grader = EmailGrader()

for i in range(10):
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    obs = env.reset()
    
    action = agent.generate_action(obs, task)
    obs, reward, done, truncated, info = env.step(action)
    
    score = grader.evaluate(env.state, task_data)

# Review all evaluations
history = grader.get_evaluation_history()
print(f"Total evaluations: {len(history)}")

for eval_record in history:
    print(f"Eval #{eval_record['evaluation_num']}: "
          f"Score={eval_record['score']:.2f} "
          f"Time={eval_record['timestamp'].strftime('%H:%M:%S')}")
    
    # Debug specific details
    if eval_record['score'] < 0.75:
        print(f"  Details: {eval_record['details']}")


BEST PRACTICES:
──────────────

1. TASK DESIGN
   ✓ Clear, unambiguous requirements
   ✓ Realistic success thresholds (0.75-0.80)
   ✓ Separated easy/medium/hard by constraint complexity
   ✓ Documented in task instruction

2. GRADER IMPLEMENTATION
   ✓ Deterministic scoring (no randomness)
   ✓ Fuzzy matching for flexible agent output
   ✓ Tolerance windows for numeric constraints
   ✓ Detailed feedback for debugging

3. AGENT TRAINING
   ✓ Use grader scores to augment environment rewards
   ✓ Start with easy tasks, progress to hard
   ✓ Log grader feedback for failure analysis
   ✓ Validate on held-out test tasks

4. INTEGRATION
   ✓ Always run grader evaluation after agent action
   ✓ Record task results for statistics
   ✓ Use grader history for auditing
   ✓ Combine step reward with grader score

5. REPRODUCIBILITY
   ✓ Use fixed seed for deterministic graders
   ✓ Test grader determinism across runs
   ✓ Document task_data parameters
   ✓ Maintain version control of task definitions
"""

# ============================================================================
# END OF GUIDE
# ============================================================================

if __name__ == "__main__":
    print(__doc__)
    print("\nFor examples, see: examples_tasks_graders.py")
    print("For tests, see: test_tasks_graders.py")
