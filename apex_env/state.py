"""
Internal state management for APEXEnv
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from apex_env.models import (
    Email,
    Meeting,
    LanguageEnum,
    GestureEnum,
)


@dataclass
class Contact:
    """Contact information"""
    contact_id: int
    name: str
    email: str
    languages: List[LanguageEnum] = field(default_factory=list)
    timezone: str = "UTC"


@dataclass
class Task:
    """Task to be completed"""
    task_id: int
    description: str
    task_type: str  # "email", "meeting", "translation", "gesture"
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    required_actions: List[str] = field(default_factory=list)
    completed_actions: Set[str] = field(default_factory=set)


@dataclass
class APEXEnvState:
    """Complete internal state of APEXEnv"""
    
    # Email system
    emails_sent: List[Email] = field(default_factory=list)
    emails_pending: List[Email] = field(default_factory=list)
    emails_failed: List[Email] = field(default_factory=list)
    
    # Calendar system
    meetings: Dict[int, Meeting] = field(default_factory=dict)
    
    # Contacts database
    contacts: Dict[int, Contact] = field(default_factory=dict)
    
    # Task management
    tasks: Dict[int, Task] = field(default_factory=dict)
    current_task_id: Optional[int] = None
    
    # Language processing
    detected_language: LanguageEnum = LanguageEnum.EN
    language_confidence: float = 1.0
    translation_history: List[tuple] = field(default_factory=list)  # (src, tgt, text)
    
    # Gesture recognition
    gesture_history: List[GestureEnum] = field(default_factory=list)
    last_gesture: Optional[GestureEnum] = None
    
    # Episode tracking
    episode_step: int = 0
    episode_reward: float = 0.0
    action_history: List[tuple] = field(default_factory=list)  # (step, action_type, success)
    error_history: List[tuple] = field(default_factory=list)  # (step, error_msg)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_action_time: datetime = field(default_factory=datetime.utcnow)

    def reset(self):
        """Reset episode state while preserving contacts"""
        self.emails_sent.clear()
        self.emails_pending.clear()
        self.emails_failed.clear()
        self.meetings.clear()
        self.tasks.clear()
        self.current_task_id = None
        self.detected_language = LanguageEnum.EN
        self.language_confidence = 1.0
        self.translation_history.clear()
        self.gesture_history.clear()
        self.last_gesture = None
        self.episode_step = 0
        self.episode_reward = 0.0
        self.action_history.clear()
        self.error_history.clear()
        self.created_at = datetime.utcnow()
        self.last_action_time = datetime.utcnow()

    def add_contact(self, contact: Contact) -> None:
        """Add contact to database"""
        self.contacts[contact.contact_id] = contact

    def get_contact(self, contact_id: int) -> Optional[Contact]:
        """Retrieve contact by ID"""
        return self.contacts.get(contact_id)

    def find_meeting_conflicts(self, meeting: Meeting) -> List[Meeting]:
        """Find conflicting meetings"""
        conflicts = []
        for existing in self.meetings.values():
            # Check time overlap
            if not (meeting.scheduled_time + timedelta(minutes=meeting.duration_minutes) 
                    <= existing.scheduled_time or
                    meeting.scheduled_time >= 
                    existing.scheduled_time + timedelta(minutes=existing.duration_minutes)):
                # Check attendee overlap
                if any(aid in existing.attendee_ids for aid in meeting.attendee_ids):
                    conflicts.append(existing)
        return conflicts

    def add_meeting(self, meeting: Meeting) -> tuple[bool, Optional[str]]:
        """Add meeting, return (success, error_msg)"""
        conflicts = self.find_meeting_conflicts(meeting)
        if conflicts:
            return False, f"Meeting conflicts with {len(conflicts)} existing meetings"
        self.meetings[meeting.meeting_id] = meeting
        return True, None

    def add_email(self, email: Email, status: str = "pending") -> tuple[bool, Optional[str]]:
        """Add email, return (success, error_msg)"""
        if status == "pending":
            self.emails_pending.append(email)
        elif status == "sent":
            self.emails_sent.append(email)
        elif status == "failed":
            self.emails_failed.append(email)
        else:
            return False, f"Invalid email status: {status}"
        return True, None

    def record_action(self, action_type: str, success: bool) -> None:
        """Record action in history"""
        self.action_history.append((self.episode_step, action_type, success))

    def record_error(self, error_msg: str) -> None:
        """Record error in history"""
        self.error_history.append((self.episode_step, error_msg))

    def get_task_progress(self, task_id: int) -> float:
        """Get task completion progress [0, 1]"""
        task = self.tasks.get(task_id)
        if not task:
            return 0.0
        if not task.required_actions:
            return 1.0 if task.completed else 0.0
        return len(task.completed_actions) / len(task.required_actions)

    def mark_task_action_complete(self, task_id: int, action_type: str) -> None:
        """Mark an action as complete for a task"""
        if task_id in self.tasks:
            self.tasks[task_id].completed_actions.add(action_type)

    def complete_task(self, task_id: int) -> None:
        """Mark task as completed"""
        if task_id in self.tasks:
            self.tasks[task_id].completed = True
            self.tasks[task_id].completed_at = datetime.utcnow()
