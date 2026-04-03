"""
Task 3 (Hard): Complex Multilingual Workflow

Agent receives multilingual or gesture-based input.
Must:
1. Recognize language/gesture intent
2. Translate if needed
3. Send confirmation email
4. Schedule follow-up meeting

This tests multi-step reasoning and language handling.
"""

from datetime import datetime, timedelta
from apex_env.state import APEXEnvState
from apex_env.tasks.base_task import BaseTask, TaskDefinition
from apex_env.models import LanguageEnum, MeetingTypeEnum


class ComplexTaskDefinition(TaskDefinition):
    """Complex workflow task metadata"""
    def __init__(self):
        super().__init__(
            task_id=3,
            name="Multilingual Workflow",
            description="Handle multilingual input, translate, send email, schedule meeting",
            difficulty="hard",
            instructions="Process input in source language, "
                        "translate to target, send confirmation email, "
                        "and schedule a follow-up meeting",
            expected_actions=["translate", "email", "meeting"],
            max_steps=20,
        )
        # Workflow requirements
        self.input_language: LanguageEnum = None
        self.target_language: LanguageEnum = None
        self.input_text: str = None
        self.recipient_id: int = None
        self.meeting_attendee_ids: list = []


class ComplexWorkflowTask(BaseTask):
    """
    Hard task: Multilingual workflow
    
    Success criteria:
    - Input language detected or translated correctly
    - Email sent in target language
    - Email contains key information from input
    - Follow-up meeting scheduled
    - Meeting time reasonable (future date)
    - All attendees included
    
    Tests: language handling, multi-step planning, coordination
    """

    def __init__(self, input_text: str, input_language: LanguageEnum,
                 target_language: LanguageEnum, recipient_id: int,
                 meeting_attendee_ids: list):
        """
        Initialize complex workflow task
        
        Args:
            input_text: Multilingual input text
            input_language: Source language
            target_language: Translation target
            recipient_id: Contact to send email to
            meeting_attendee_ids: Contacts for follow-up meeting
        """
        task_def = ComplexTaskDefinition()
        super().__init__(task_def)
        
        self.task_def.input_text = input_text
        self.task_def.input_language = input_language
        self.task_def.target_language = target_language
        self.task_def.recipient_id = recipient_id
        self.task_def.meeting_attendee_ids = meeting_attendee_ids

    def get_instruction(self) -> str:
        """Return multi-step instruction"""
        return (
            f"Process multilingual workflow:\n"
            f"1. Input text: '{self.task_def.input_text}' (in {self.task_def.input_language.value})\n"
            f"2. Translate to {self.task_def.target_language.value}\n"
            f"3. Send confirmation email to contact {self.task_def.recipient_id}\n"
            f"4. Schedule follow-up meeting with "
            f"{len(self.task_def.meeting_attendee_ids)} attendees"
        )

    def evaluate(self, state: APEXEnvState) -> float:
        """
        Evaluate complex workflow completion.
        
        Scoring breakdown:
        - 0.15: Translation attempted in target language
        - 0.25: Email sent to correct recipient after translation
        - 0.25: Email contains content relevant to input
        - 0.20: Meeting scheduled
        - 0.15: Meeting includes required attendees
        
        Must score >= 0.80 for success
        """
        score = 0.0
        
        # 1. Check translation (0.15 points)
        if state.translation_history:
            # Find translation in workflow
            for src, tgt, text in state.translation_history:
                if (src == self.task_def.input_language and 
                    tgt == self.task_def.target_language and
                    len(text) > 5):
                    score += 0.15
                    break
        
        # 2. Check email (0.50 points total)
        recent_emails = [
            e for e in state.emails_sent
            if e.timestamp > self.started_at
        ]
        
        if recent_emails:
            email = recent_emails[-1]
            
            # Email to correct recipient: 0.25
            if email.sender_id == 0:  # Agent sender
                score += 0.20
            
            # Email in target language: 0.05
            if email.language == self.task_def.target_language:
                score += 0.05
            
            # Email contains relevant content: 0.25
            email_words = email.body.lower().split()
            input_keywords = self.task_def.input_text.lower().split()[:4]
            
            keyword_matches = sum(
                1 for kw in input_keywords
                if any(kw in word for word in email_words)
            )
            
            if keyword_matches >= 2:
                score += 0.25
            else:
                # Partial credit
                score += 0.25 * (keyword_matches / 4)
        
        # 3. Check meeting (0.35 points)
        if state.meetings:
            meetings_after_task = [
                m for m in state.meetings.values()
                if m.created_at > self.started_at
            ]
            
            if meetings_after_task:
                meeting = meetings_after_task[-1]
                
                # Meeting scheduled: 0.20
                score += 0.20
                
                # Time is in future: 0.05
                if meeting.scheduled_time > datetime.utcnow():
                    score += 0.05
                
                # Attendees included: 0.10
                required_attendees = set(self.task_def.meeting_attendee_ids)
                actual_attendees = set(meeting.attendee_ids)
                
                if required_attendees.issubset(actual_attendees):
                    score += 0.10
                elif actual_attendees & required_attendees:
                    overlap = len(actual_attendees & required_attendees)
                    score += 0.10 * (overlap / len(required_attendees))
        
        return min(1.0, score)

    def is_success(self, state: APEXEnvState) -> bool:
        """
        Check if complex workflow succeeded.
        Success: all steps completed with score >= 0.80
        """
        if not state.emails_sent or not state.meetings or not state.translation_history:
            return False
        
        return self.evaluate(state) >= 0.80
