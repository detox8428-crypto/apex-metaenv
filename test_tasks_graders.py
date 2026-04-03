"""
Integration tests for tasks and graders

Validates:
1. Task creation and evaluation workflows
2. Grader determinism (same input → same score)
3. Scoring accuracy across different scenarios
4. Multi-step workflow coordination
5. Error handling and edge cases
"""

import unittest
from datetime import datetime, timedelta
from apex_env import APEXEnv, EnvironmentConfig, EmailAction, MeetingAction, TranslationAction
from apex_env.tasks import EmailTask, MeetingTask, ComplexWorkflowTask
from apex_env.graders import EmailGrader, MeetingGrader, WorkflowGrader
from apex_env.models import LanguageEnum, MeetingTypeEnum, PriorityEnum


class TestEmailTask(unittest.TestCase):
    """Test EmailTask (Easy)"""
    
    def setUp(self):
        self.env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5, seed=42))
        self.env.reset()
        self.grader = EmailGrader()
    
    def test_email_task_perfect_match(self):
        """Test: Perfect email matching all criteria"""
        task_data = {
            "expected_recipient_id": 0,
            "expected_subject": "Meeting Request",
            "expected_body": "schedule a meeting",
            "expected_language": LanguageEnum.EN,
            "subject_keywords": ["meeting", "request"],
            "body_keywords": ["schedule", "meeting"],
        }
        
        action = EmailAction(
            recipient_id=0,
            subject="Meeting Request",
            body="Please schedule a meeting tomorrow",
            language=LanguageEnum.EN,
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be high score (1.0 for recipient, near 1.0 for subject/body)
        self.assertGreater(score, 0.9)
    
    def test_email_task_partial_match(self):
        """Test: Partial email matching"""
        task_data = {
            "expected_recipient_id": 0,
            "expected_subject": "Meeting Request",
            "expected_body": "schedule a meeting",
            "expected_language": LanguageEnum.EN,
        }
        
        action = EmailAction(
            recipient_id=0,
            subject="Hello",  # Different subject
            body="meeting",   # Partial body
            language=LanguageEnum.EN,
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be moderate score (recipient OK, subject bad, body OK)
        self.assertGreater(score, 0.3)
        self.assertLess(score, 0.8)
    
    def test_email_task_wrong_recipient(self):
        """Test: Email to wrong recipient"""
        task_data = {
            "expected_recipient_id": 0,
            "expected_subject": "Meeting",
            "expected_body": "meeting",
            "expected_language": LanguageEnum.EN,
        }
        
        action = EmailAction(
            recipient_id=5,  # Wrong recipient ID
            subject="Meeting",
            body="meeting content",
            language=LanguageEnum.EN,
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be low score (recipient is 30% of score)
        self.assertLess(score, 0.8)
    
    def test_email_task_wrong_language(self):
        """Test: Email in wrong language"""
        task_data = {
            "expected_recipient_id": 0,
            "expected_subject": "Meeting",
            "expected_body": "meeting",
            "expected_language": LanguageEnum.EN,
        }
        
        action = EmailAction(
            recipient_id=0,
            subject="Meeting",
            body="meeting",
            language=LanguageEnum.ES,  # Wrong language
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be lower score (language is 10% of score)
        self.assertGreater(score, 0.7)
        self.assertLess(score, 1.0)


class TestMeetingTask(unittest.TestCase):
    """Test MeetingTask (Medium)"""
    
    def setUp(self):
        self.env = APEXEnv(config=EnvironmentConfig(max_episode_steps=5, seed=42))
        self.env.reset()
        self.grader = MeetingGrader()
        self.target_date = datetime.utcnow() + timedelta(days=3)
    
    def test_meeting_task_perfect_match(self):
        """Test: Perfect meeting matching all criteria"""
        target_time = self.target_date.replace(hour=14, minute=0)
        
        task_data = {
            "expected_date": self.target_date,
            "expected_time_window": (9, 17),
            "expected_attendee_ids": [0, 1, 2],
            "expected_duration": 60,
            "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
            "tolerance_minutes": 15,
        }
        
        action = MeetingAction(
            title="Q2 Planning",
            attendee_ids=[0, 1, 2],
            scheduled_time=target_time,
            duration_minutes=60,
            meeting_type=MeetingTypeEnum.VIRTUAL,
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be high score
        self.assertGreater(score, 0.95)
    
    def test_meeting_task_adjacent_date(self):
        """Test: Meeting on adjacent day"""
        adjacent_date = self.target_date + timedelta(days=1)
        adjacent_time = adjacent_date.replace(hour=14, minute=0)
        
        task_data = {
            "expected_date": self.target_date,
            "expected_time_window": (9, 17),
            "expected_attendee_ids": [0, 1, 2],
            "expected_duration": 60,
            "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
        }
        
        action = MeetingAction(
            title="Q2 Planning",
            attendee_ids=[0, 1, 2],
            scheduled_time=adjacent_time,
            duration_minutes=60,
            meeting_type=MeetingTypeEnum.VIRTUAL,
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be partial score (adjacent day: ~40% of date score)
        self.assertGreater(score, 0.7)
        self.assertLess(score, 0.95)
    
    def test_meeting_task_partial_attendees(self):
        """Test: Meeting with subset of required attendees"""
        target_time = self.target_date.replace(hour=14, minute=0)
        
        task_data = {
            "expected_date": self.target_date,
            "expected_time_window": (9, 17),
            "expected_attendee_ids": [0, 1, 2],
            "expected_duration": 60,
            "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
        }
        
        action = MeetingAction(
            title="Q2 Planning",
            attendee_ids=[0, 1],  # Only 2 of 3 required
            scheduled_time=target_time,
            duration_minutes=60,
            meeting_type=MeetingTypeEnum.VIRTUAL,
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be lowered (attendees are 15% of score, but prorated)
        self.assertGreater(score, 0.7)
        self.assertLess(score, 0.95)
    
    def test_meeting_task_time_outside_window(self):
        """Test: Meeting outside time window"""
        target_time = self.target_date.replace(hour=19, minute=0)  # 7 PM, outside 9-5
        
        task_data = {
            "expected_date": self.target_date,
            "expected_time_window": (9, 17),
            "expected_attendee_ids": [0, 1, 2],
            "expected_duration": 60,
            "expected_meeting_type": MeetingTypeEnum.VIRTUAL,
        }
        
        action = MeetingAction(
            title="Q2 Planning",
            attendee_ids=[0, 1, 2],
            scheduled_time=target_time,
            duration_minutes=60,
            meeting_type=MeetingTypeEnum.VIRTUAL,
        )
        
        self.env.step(action)
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be lower score (time is 20% of score)
        self.assertGreater(score, 0.6)
        self.assertLess(score, 0.95)


class TestWorkflowTask(unittest.TestCase):
    """Test ComplexWorkflowTask (Hard)"""
    
    def setUp(self):
        self.env = APEXEnv(config=EnvironmentConfig(max_episode_steps=10, seed=42))
        self.env.reset()
        self.grader = WorkflowGrader()
    
    def test_workflow_three_step_complete(self):
        """Test: Complete 3-step workflow"""
        meeting_time = datetime.utcnow() + timedelta(days=1)
        
        # Step 1: Translate
        action1 = TranslationAction(
            text="Good morning",
            source_language=LanguageEnum.EN,
            target_language=LanguageEnum.ES,
        )
        self.env.step(action1)
        
        # Step 2: Email
        action2 = EmailAction(
            recipient_id=0,
            subject="Buenos Días",
            body="Buenos días a todos",
            language=LanguageEnum.ES,
        )
        self.env.step(action2)
        
        # Step 3: Meeting
        action3 = MeetingAction(
            title="Reunión",
            attendee_ids=[0, 1],
            scheduled_time=meeting_time,
            duration_minutes=60,
            meeting_type=MeetingTypeEnum.VIRTUAL,
        )
        self.env.step(action3)
        
        # Evaluate
        task_data = {
            "steps": ["translate", "email", "meeting"],
            "step_1_data": {"source_language": LanguageEnum.EN, "target_language": LanguageEnum.ES},
            "step_2_data": {
                "expected_recipient_id": 0,
                "expected_subject": "Buenos",
                "expected_body": "Buenos días",
                "expected_language": LanguageEnum.ES,
            },
            "step_3_data": {
                "expected_date": meeting_time,
                "expected_time_window": (9, 17),
                "expected_attendee_ids": [0, 1],
            },
        }
        
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be high score for complete workflow
        self.assertGreater(score, 0.7)
    
    def test_workflow_two_step(self):
        """Test: 2-step workflow (email + meeting only)"""
        meeting_time = datetime.utcnow() + timedelta(days=1)
        
        # Skip translation, do email and meeting
        action1 = EmailAction(
            recipient_id=0,
            subject="Meeting",
            body="meeting content",
            language=LanguageEnum.EN,
        )
        self.env.step(action1)
        
        action2 = MeetingAction(
            title="Meeting",
            attendee_ids=[0],
            scheduled_time=meeting_time,
            duration_minutes=60,
            meeting_type=MeetingTypeEnum.VIRTUAL,
        )
        self.env.step(action2)
        
        # Evaluate
        task_data = {
            "steps": ["email", "meeting"],
            "step_1_data": {
                "expected_recipient_id": 0,
                "expected_subject": "Meeting",
                "expected_body": "meeting",
            },
            "step_2_data": {
                "expected_date": meeting_time,
                "expected_attendee_ids": [0],
            },
        }
        
        score = self.grader.evaluate(self.env.state, task_data)
        
        # Should be score for 2 steps (different weighting than 3 steps)
        self.assertGreater(score, 0.3)


class TestGraderDeterminism(unittest.TestCase):
    """Test that graders are deterministic (reproducible scoring)"""
    
    def test_email_grader_determinism(self):
        """Test: EmailGrader produces consistent scores"""
        grader = EmailGrader()
        
        results = []
        for _ in range(3):
            env = APEXEnv(config=EnvironmentConfig(seed=42))
            env.reset()
            
            action = EmailAction(
                recipient_id=0,
                subject="Test Subject",
                body="test content",
                language=LanguageEnum.EN,
            )
            env.step(action)
            
            task_data = {
                "expected_recipient_id": 0,
                "expected_subject": "Test",
                "expected_body": "content",
                "expected_language": LanguageEnum.EN,
            }
            
            score = grader.evaluate(env.state, task_data)
            results.append(score)
        
        # All scores should be identical
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
    
    def test_meeting_grader_determinism(self):
        """Test: MeetingGrader produces consistent scores"""
        grader = MeetingGrader()
        target_date = datetime.utcnow() + timedelta(days=3)
        target_time = target_date.replace(hour=14, minute=0)
        
        results = []
        for _ in range(3):
            env = APEXEnv(config=EnvironmentConfig(seed=42))
            env.reset()
            
            action = MeetingAction(
                title="Test Meeting",
                attendee_ids=[0, 1],
                scheduled_time=target_time,
                duration_minutes=60,
                meeting_type=MeetingTypeEnum.VIRTUAL,
            )
            env.step(action)
            
            task_data = {
                "expected_date": target_date,
                "expected_time_window": (9, 17),
                "expected_attendee_ids": [0, 1],
                "expected_duration": 60,
            }
            
            score = grader.evaluate(env.state, task_data)
            results.append(score)
        
        # All scores should be identical
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])


class TestGraderEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_email_grader_empty_recipient_list(self):
        """Test: Grader handles state with no emails"""
        env = APEXEnv(config=EnvironmentConfig(seed=42))
        env.reset()
        # Don't send any emails
        
        grader = EmailGrader()
        task_data = {
            "expected_recipient_id": 0,
            "expected_subject": "Test",
            "expected_body": "test",
        }
        
        score = grader.evaluate(env.state, task_data)
        
        # Should return 0 score for no emails sent
        self.assertEqual(score, 0.0)
    
    def test_meeting_grader_empty_calendar(self):
        """Test: Grader handles state with no meetings"""
        env = APEXEnv(config=EnvironmentConfig(seed=42))
        env.reset()
        # Don't schedule any meetings
        
        grader = MeetingGrader()
        task_data = {
            "expected_date": datetime.utcnow() + timedelta(days=1),
            "expected_attendee_ids": [0],
        }
        
        score = grader.evaluate(env.state, task_data)
        
        # Should return partial score (0.2 for "meeting_scheduled" = 0)
        self.assertLess(score, 0.5)


class TestTaskMetrics(unittest.TestCase):
    """Test task tracking and metrics"""
    
    def test_task_duration_tracking(self):
        """Test: Task tracks execution duration"""
        task = EmailTask(
            recipient_id=0,
            subject="Test",
            body="content",
        )
        
        import time
        time.sleep(0.1)
        task.mark_complete()
        
        duration = task.get_duration()
        self.assertGreater(duration, 0.0)
    
    def test_task_success_determination(self):
        """Test: Task correctly determines success"""
        task = EmailTask(recipient_id=0, subject="Test", body="content")
        
        env = APEXEnv(config=EnvironmentConfig(seed=42))
        env.reset()
        
        grader = EmailGrader()
        
        # Send matching email
        action = EmailAction(
            recipient_id=0,
            subject="Test",
            body="content",
            language=LanguageEnum.EN,
        )
        env.step(action)
        
        task_data = {
            "expected_recipient_id": 0,
            "expected_subject": "Test",
            "expected_body": "content",
        }
        
        score = grader.evaluate(env.state, task_data)
        task.evaluate_score = score
        task.mark_complete()
        
        # Score > 0.75 means success
        is_success = score >= 0.75
        self.assertTrue(is_success)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
