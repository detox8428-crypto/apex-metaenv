"""
Examples demonstrating APEXEnv tasks and graders

Shows how to:
1. Create and use different task types (Easy, Medium, Hard)
2. Evaluate tasks with graders
3. Interpret grader feedback
"""

from datetime import datetime, timedelta
from apex_env import APEXEnv, EnvironmentConfig, EmailAction, MeetingAction, TranslationAction
from apex_env.tasks import EmailTask, MeetingTask, ComplexWorkflowTask
from apex_env.graders import EmailGrader, MeetingGrader, WorkflowGrader
from apex_env.models import LanguageEnum, MeetingTypeEnum


def example_1_email_task_easy():
    """Example 1: Easy task - Send email"""
    print("=" * 70)
    print("EXAMPLE 1: Email Task (Easy)")
    print("=" * 70)
    
    # Create task
    task = EmailTask(
        recipient_id=0,
        subject="Meeting Request",
        body="schedule a meeting",
        language=LanguageEnum.EN,
    )
    
    print(f"Task: {task.get_instruction()}")
    print()
    
    # Setup environment
    env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5))
    env.reset()
    
    # Agent executes action
    action = EmailAction(
        recipient_id=0,
        subject="Meeting Request for Tomorrow",
        body="I would like to schedule a meeting tomorrow to discuss the project.",
        language=LanguageEnum.EN,
    )
    
    obs, reward, done, truncated, info = env.step(action)
    print(f"✓ Email sent")
    print(f"  - Recipient ID: 0")
    print(f"  - Subject: {action.subject}")
    print()
    
    # Evaluate with grader
    grader = EmailGrader()
    
    task_data = {
        "expected_recipient_id": 0,
        "expected_subject": "Meeting Request",
        "expected_body": "schedule a meeting",
        "expected_language": LanguageEnum.EN,
        "subject_keywords": ["meeting", "request"],
        "body_keywords": ["schedule", "meeting"],
    }
    
    score = grader.evaluate(env.state, task_data)
    feedback = grader.get_detailed_feedback()
    
    print(f"Grader Evaluation:")
    print(f"  Score: {score:.2f}/1.00")
    print(feedback)
    print()


def example_2_meeting_task_medium():
    """Example 2: Medium task - Schedule meeting with constraints"""
    print("=" * 70)
    print("EXAMPLE 2: Meeting Task (Medium)")
    print("=" * 70)
    
    # Create task
    target_date = datetime.utcnow() + timedelta(days=3)
    task = MeetingTask(
        attendee_ids=[0, 1, 2],
        target_date=target_date,
        time_window=(9, 17),  # 9 AM to 5 PM
        duration_minutes=60,
        meeting_type=MeetingTypeEnum.VIRTUAL,
        title="Q2 Planning",
    )
    
    print(f"Task: {task.get_instruction()}")
    print()
    
    # Setup environment
    env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5))
    env.reset()
    
    # Agent executes action
    meeting_time = target_date.replace(hour=14, minute=0)  # 2 PM
    
    action = MeetingAction(
        title="Q2 Planning Session",
        attendee_ids=[0, 1, 2],
        scheduled_time=meeting_time,
        duration_minutes=60,
        meeting_type=MeetingTypeEnum.VIRTUAL,
        description="Quarterly planning and roadmap discussion",
    )
    
    obs, reward, done, truncated, info = env.step(action)
    print(f"✓ Meeting scheduled")
    print(f"  - Title: {action.title}")
    print(f"  - Attendees: {len(action.attendee_ids)}")
    print(f"  - Time: {meeting_time.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Evaluate with grader
    grader = MeetingGrader()
    
    task_data = {
        "expected_date": target_date,
        "expected_time_window": (9, 17),
        "expected_attendee_ids": [0, 1, 2],
        "expected_duration": 60,
        "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
        "tolerance_minutes": 15,
    }
    
    score = grader.evaluate(env.state, task_data)
    feedback = grader.get_detailed_feedback()
    
    print(f"Grader Evaluation:")
    print(f"  Score: {score:.2f}/1.00")
    print(feedback)
    print()


def example_3_workflow_task_hard():
    """Example 3: Hard task - Multilingual workflow"""
    print("=" * 70)
    print("EXAMPLE 3: Complex Workflow Task (Hard)")
    print("=" * 70)
    
    # Create task
    task = ComplexWorkflowTask(
        input_text="Good morning. I would like to schedule a meeting.",
        input_language=LanguageEnum.EN,
        target_language=LanguageEnum.ES,
        recipient_id=0,
        meeting_attendee_ids=[0, 1],
    )
    
    print(f"Task: {task.get_instruction()}")
    print()
    
    # Setup environment
    env = APEXEnv(config=EnvironmentConfig(max_episode_steps=10))
    env.reset()
    
    # Step 1: Translate
    print("Step 1: Translation")
    action1 = TranslationAction(
        text="Good morning. I would like to schedule a meeting.",
        source_language=LanguageEnum.EN,
        target_language=LanguageEnum.ES,
    )
    obs, reward, done, truncated, info = env.step(action1)
    print(f"  ✓ Translated EN → ES")
    print()
    
    # Step 2: Send email
    print("Step 2: Email")
    action2 = EmailAction(
        recipient_id=0,
        subject="Solicitud de Reunión",
        body="Buenos días. Quisiera agendar una reunión para discutir nuestros planes.",
        language=LanguageEnum.ES,
    )
    obs, reward, done, truncated, info = env.step(action2)
    print(f"  ✓ Email sent in Spanish")
    print()
    
    # Step 3: Schedule meeting
    print("Step 3: Meeting")
    meeting_time = datetime.utcnow() + timedelta(days=1, hours=2)
    action3 = MeetingAction(
        title="Planificación de Proyecto",
        attendee_ids=[0, 1],
        scheduled_time=meeting_time,
        duration_minutes=60,
        meeting_type=MeetingTypeEnum.VIRTUAL,
    )
    obs, reward, done, truncated, info = env.step(action3)
    print(f"  ✓ Meeting scheduled")
    print()
    
    # Evaluate with grader
    grader = WorkflowGrader()
    
    task_data = {
        "steps": ["translate", "email", "meeting"],
        "step_1_data": {
            "source_language": LanguageEnum.EN,
            "target_language": LanguageEnum.ES,
        },
        "step_2_data": {
            "expected_recipient_id": 0,
            "expected_subject": "Solicitud",
            "expected_body": "reunión",
            "expected_language": LanguageEnum.ES,
            "subject_keywords": ["solicitud", "reunión"],
            "body_keywords": ["quisiera", "agendar"],
        },
        "step_3_data": {
            "expected_date": meeting_time,
            "expected_time_window": (9, 17),
            "expected_attendee_ids": [0, 1],
            "expected_duration": 60,
            "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
        },
    }
    
    score = grader.evaluate(env.state, task_data)
    feedback = grader.get_detailed_feedback()
    
    print(f"Workflow Grader Evaluation:")
    print(f"  Score: {score:.2f}/1.00")
    print(feedback)
    print()


def example_4_task_evaluation_cycle():
    """Example 4: Complete task evaluation cycle"""
    print("=" * 70)
    print("EXAMPLE 4: Complete Task Evaluation Cycle")
    print("=" * 70)
    
    # Setup
    env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5, seed=42))
    obs = env.reset()
    
    # Create task
    task = EmailTask(
        recipient_id=5,
        subject="Project Update",
        body="Please review the latest changes",
        language=LanguageEnum.EN,
    )
    
    print(f"Task Created: {task.task_def.name}")
    print(f"Description: {task.task_def.description}")
    print(f"Difficulty: {task.task_def.difficulty}")
    print()
    
    # ExecuteAction
    print("Executing task...")
    action = EmailAction(
        recipient_id=5,
        subject="Project Update - Review Required",
        body="Please review the latest code changes and provide feedback.",
        language=LanguageEnum.EN,
    )
    
    obs, reward, done, truncated, info = env.step(action)
    task.record_action("email", info['action_result']['success'])
    
    print(f"  Action: Email sent")
    print(f"  Success: {info['action_result']['success']}")
    print()
    
    # Evaluate
    print("Evaluating task...")
    grader = EmailGrader()
    
    task_data = {
        "expected_recipient_id": 5,
        "expected_subject": "Project Update",
        "expected_body": "review the latest",
        "expected_language": LanguageEnum.EN,
        "subject_keywords": ["project", "update"],
        "body_keywords": ["review", "changes"],
    }
    
    score = grader.evaluate(env.state, task_data)
    task.evaluate_score = score
    
    print(f"  Grader Score: {score:.2f}/1.00")
    
    # Determine success
    task.mark_complete()
    success = score >= 0.75
    
    print(f"  Task Success: {success}")
    print(f"  Task Duration: {task.get_duration():.2f} seconds")
    print()
    
    # Get detailed feedback
    print("Detailed Feedback:")
    print(grader.get_detailed_feedback())
    print()


def example_5_grader_history():
    """Example 5: Grader evaluation history"""
    print("=" * 70)
    print("EXAMPLE 5: Grader Evaluation History")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    env.reset()
    
    grader = EmailGrader()
    
    # Perform multiple evaluations
    for i in range(3):
        # Send different emails
        action = EmailAction(
            recipient_id=i,
            subject=f"Email {i}",
            body=f"Content {i}",
            language=LanguageEnum.EN,
        )
        obs, reward, done, trunc, info = env.step(action)
        
        # Evaluate
        task_data = {
            "expected_recipient_id": i,
            "expected_subject": f"Email",
            "expected_body": f"Content",
            "expected_language": LanguageEnum.EN,
        }
        
        score = grader.evaluate(env.state, task_data)
        print(f"Evaluation {i+1}: Score = {score:.2f}")
    
    print()
    print(f"Total Evaluations: {grader.evaluation_count}")
    
    # Get history
    history = grader.get_evaluation_history()
    print(f"\nHistory:")
    for eval in history:
        print(f"  Eval #{eval['evaluation_num']}: {eval['score']:.2f} - {eval['timestamp'].strftime('%H:%M:%S')}")
    print()


def example_6_scoring_breakdown():
    """Example 6: Understanding scoring components"""
    print("=" * 70)
    print("EXAMPLE 6: Understanding Grader Scoring Breakdown")
    print("=" * 70)
    
    env = APEXEnv(config=EnvironmentConfig(seed=42))
    env.reset()
    
    # Send email with partial match
    action = EmailAction(
        recipient_id=0,
        subject="Hello World",  # Doesn't match expected "Meeting"
        body="This is a test email",
        language=LanguageEnum.EN,
    )
    
    obs, reward, done, trunc, info = env.step(action)
    
    # Evaluate
    grader = EmailGrader()
    task_data = {
        "expected_recipient_id": 0,
        "expected_subject": "Meeting Request",  # Mismatch
        "expected_body": "Please schedule",     # Mismatch
        "expected_language": LanguageEnum.EN,   # Match
        "subject_keywords": ["meeting", "request"],
        "body_keywords": ["schedule", "please"],
    }
    
    score = grader.evaluate(env.state, task_data)
    
    print(f"Email Content:")
    print(f"  Subject: 'Hello World' (expected: 'Meeting Request')")
    print(f"  Body: 'This is a test email' (expected: 'Please schedule...')")
    print(f"  Language: EN (expected: EN)")
    print()
    
    print(f"Scoring Components:")
    eval_history = grader.get_evaluation_history()
    last_eval = eval_history[-1]
    details = last_eval["details"]
    
    print(f"  Recipient Match: {details.get('recipient_score', 0):.2f}/0.30")
    print(f"  Subject Match: {details.get('subject_score', 0):.2f}/0.25")
    print(f"  Body Match: {details.get('body_score', 0):.2f}/0.25")
    print(f"  Language Match: {details.get('language_score', 0):.2f}/0.10")
    print(f"  Format Quality: {details.get('format_score', 0):.2f}/0.10")
    print(f"  ─────────────────────────────────────")
    print(f"  TOTAL: {score:.2f}/1.00")
    print()
    
    print(grader.get_detailed_feedback())
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  APEX ENVIRONMENT - TASKS & GRADERS EXAMPLES".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    examples = [
        example_1_email_task_easy,
        example_2_meeting_task_medium,
        example_3_workflow_task_hard,
        example_4_task_evaluation_cycle,
        example_5_grader_history,
        example_6_scoring_breakdown,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
