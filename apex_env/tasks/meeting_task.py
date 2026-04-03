"""
Task 2 (Medium): Schedule Meeting

Agent receives meeting requirements with constraints:
- Attendees to invite
- Time window or specific date/time
- Duration
- Meeting type

Must avoid conflicts and schedule within constraints.
"""

from datetime import datetime, timedelta
from apex_env.state import APEXEnvState
from apex_env.tasks.base_task import BaseTask, TaskDefinition
from apex_env.models import MeetingTypeEnum


class MeetingTaskDefinition(TaskDefinition):
    """Meeting task metadata"""
    def __init__(self):
        super().__init__(
            task_id=2,
            name="Schedule Meeting",
            description="Schedule a meeting with specified attendees and constraints",
            difficulty="medium",
            instructions="Schedule a meeting with given attendees, "
                        "time window, and meeting type",
            expected_actions=["meeting"],
            max_steps=10,
        )
        # Meeting-specific requirements
        self.attendee_ids: list = []
        self.target_date: datetime = None
        self.time_window: tuple = None  # (start_hour, end_hour) in 24h format
        self.duration_minutes: int = 60
        self.meeting_type: MeetingTypeEnum = MeetingTypeEnum.VIRTUAL
        self.title: str = None


class MeetingTask(BaseTask):
    """
    Medium task: Schedule meeting with constraints
    
    Success criteria:
    - Meeting scheduled at reasonable time
    - All attendees included
    - No conflicts with existing meetings
    - Duration matches requirement
    - Meeting type correct
    """

    def __init__(self, attendee_ids: list, target_date: datetime,
                 time_window: tuple = (9, 17), duration_minutes: int = 60,
                 meeting_type: MeetingTypeEnum = MeetingTypeEnum.VIRTUAL,
                 title: str = "Team Sync"):
        """
        Initialize meeting task
        
        Args:
            attendee_ids: List of contact IDs to invite
            target_date: Date for meeting (within this day)
            time_window: (start_hour, end_hour) in 24h format, e.g. (9, 17)
            duration_minutes: Meeting duration
            meeting_type: VIRTUAL, IN_PERSON, HYBRID
            title: Meeting title
        """
        task_def = MeetingTaskDefinition()
        super().__init__(task_def)
        
        self.task_def.attendee_ids = attendee_ids
        self.task_def.target_date = target_date
        self.task_def.time_window = time_window
        self.task_def.duration_minutes = duration_minutes
        self.task_def.meeting_type = meeting_type
        self.task_def.title = title

    def get_instruction(self) -> str:
        """Return instruction to agent"""
        attendee_str = ", ".join(str(id) for id in self.task_def.attendee_ids[:3])
        if len(self.task_def.attendee_ids) > 3:
            attendee_str += f", ... ({len(self.task_def.attendee_ids)} total)"
        
        return (
            f"Schedule a {self.task_def.duration_minutes}-minute {self.task_def.meeting_type.value} "
            f"meeting on {self.task_def.target_date.strftime('%Y-%m-%d')} "
            f"between {self.task_def.time_window[0]:02d}:00 and {self.task_def.time_window[1]:02d}:00 "
            f"with attendees: {attendee_str}"
        )

    def _is_time_in_window(self, meeting_time: datetime) -> bool:
        """Check if meeting time is within specified window"""
        start_hour, end_hour = self.task_def.time_window
        meeting_hour = meeting_time.hour
        
        # Must be within window
        if not (start_hour <= meeting_hour < end_hour):
            return False
        
        # Must fit duration in window
        end_min = meeting_hour + (meeting_time.minute + self.task_def.duration_minutes) // 60
        return end_min <= end_hour

    def _is_date_match(self, meeting_time: datetime) -> bool:
        """Check if meeting date matches target date"""
        target = self.task_def.target_date.date()
        meeting = meeting_time.date()
        return target == meeting

    def evaluate(self, state: APEXEnvState) -> float:
        """
        Evaluate meeting task completion.
        
        Scoring:
        - 0.0: No meeting scheduled
        - 0.20: Meeting scheduled but wrong date
        - 0.40: Correct date but wrong time window
        - 0.60: Correct date/time but incomplete attendees
        - 0.80: Correct date/time/attendees but wrong duration/type
        - 1.0: Perfect match
        """
        if not state.meetings:
            return 0.0
        
        # Find meeting scheduled after task start
        recent_meetings = [
            m for m in state.meetings.values()
            if m.created_at > self.started_at
        ]
        
        if not recent_meetings:
            return 0.0
        
        meeting = recent_meetings[-1]  # Last scheduled meeting
        score = 0.0
        
        # Date match (0.20 base points)
        if self._is_date_match(meeting.scheduled_time):
            score += 0.20
        
            # Time window match (additional 0.20)
            if self._is_time_in_window(meeting.scheduled_time):
                score += 0.20
        
        # Attendees match (0.30 points)
        expected_attendees = set(self.task_def.attendee_ids)
        actual_attendees = set(meeting.attendee_ids)
        
        if expected_attendees.issubset(actual_attendees):
            score += 0.30  # All required attendees
        elif actual_attendees & expected_attendees:
            overlap = len(actual_attendees & expected_attendees)
            required = len(expected_attendees)
            score += 0.30 * (overlap / required)
        
        # Duration match (0.15 points)
        duration_tolerance = 15  # ±15 minutes acceptable
        if abs(meeting.duration_minutes - self.task_def.duration_minutes) <= duration_tolerance:
            score += 0.15
        
        # Meeting type match (0.15 points)
        if meeting.meeting_type == self.task_def.meeting_type:
            score += 0.15
        
        return min(1.0, score)

    def is_success(self, state: APEXEnvState) -> bool:
        """
        Check if meeting task succeeded.
        Success: score >= 0.80 (all key criteria met)
        """
        return self.evaluate(state) >= 0.80
