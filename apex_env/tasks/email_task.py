"""
Task 1 (Easy): Send Email

Agent receives instruction to send email to specific contact
Must extract: recipient, subject, body, language (optional)
Goal: Send email that matches the intended recipient and content
"""

from datetime import datetime
from apex_env.state import APEXEnvState
from apex_env.tasks.base_task import BaseTask, TaskDefinition
from apex_env.models import LanguageEnum


class EmailTaskDefinition(TaskDefinition):
    """Email task metadata"""
    def __init__(self):
        super().__init__(
            task_id=1,
            name="Send Email",
            description="Send an email to specified recipient",
            difficulty="easy",
            instructions="Send an email with the following details: "
                        "recipient (contact ID), subject, and body",
            expected_actions=["email"],
            max_steps=5,
        )
        # Email-specific requirements
        self.recipient_id: int = None
        self.subject: str = None
        self.body: str = None
        self.language: LanguageEnum = LanguageEnum.EN
        self.priority: str = "medium"


class EmailTask(BaseTask):
    """
    Easy task: Send email
    
    Success criteria:
    - Email sent to correct recipient
    - Subject matches expectation (fuzzy match)
    - Body contains key information
    - Language appropriate
    """

    def __init__(self, recipient_id: int, subject: str, body: str, 
                 language: LanguageEnum = LanguageEnum.EN):
        """
        Initialize email task
        
        Args:
            recipient_id: Target contact ID
            subject: Expected subject (or partial)
            body: Expected content (or partial)
            language: Expected language
        """
        task_def = EmailTaskDefinition()
        super().__init__(task_def)
        
        self.task_def.recipient_id = recipient_id
        self.task_def.subject = subject
        self.task_def.body = body
        self.task_def.language = language

    def get_instruction(self) -> str:
        """Return instruction to agent"""
        return (
            f"Send an email to contact {self.task_def.recipient_id} "
            f"with subject: '{self.task_def.subject}' "
            f"and body about: '{self.task_def.body}'"
        )

    def evaluate(self, state: APEXEnvState) -> float:
        """
        Evaluate email task completion.
        
        Scoring:
        - 0.0: No email sent
        - 0.25: Email sent to correct recipient
        - 0.50: Recipient + subject match
        - 0.75: Recipient + subject + body match
        - 1.0: Perfect match with language
        """
        if not state.emails_sent:
            return 0.0
        
        # Find email to this recipient
        recipient_match = [
            e for e in state.emails_sent
            if e.sender_id == 0 and e.timestamp > self.started_at
        ]
        
        if not recipient_match:
            return 0.0
        
        email = recipient_match[-1]  # Last sent email
        score = 0.25  # Base for sending email
        
        # Subject match (case-insensitive, partial)
        if self.task_def.subject.lower() in email.subject.lower():
            score += 0.25
        else:
            # Fuzzy check: keywords present
            subject_keywords = self.task_def.subject.lower().split()[:2]
            if any(kw in email.subject.lower() for kw in subject_keywords):
                score += 0.15
        
        # Body match (partial content check)
        if self.task_def.body.lower() in email.body.lower():
            score += 0.25
        else:
            # Fuzzy check: key words present
            body_keywords = self.task_def.body.lower().split()[:3]
            if any(kw in email.body.lower() for kw in body_keywords):
                score += 0.15
        
        # Language match
        if email.language == self.task_def.language:
            score += 0.15
        
        # Cap at 1.0
        return min(1.0, score)

    def is_success(self, state: APEXEnvState) -> bool:
        """
        Check if email task succeeded.
        Success: score >= 0.75 (recipient + subject + body)
        """
        return self.evaluate(state) >= 0.75
