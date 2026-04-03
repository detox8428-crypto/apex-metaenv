"""
Meeting grader for APEXEnv

Evaluates meeting scheduling correctness and quality.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from apex_env.state import APEXEnvState
from apex_env.graders.base_grader import BaseGrader


class MeetingGrader(BaseGrader):
    """
    Grader for meeting scheduling task evaluation.
    
    Scoring criteria:
    - Meeting scheduled (0.20)
    - Date correctness (0.25)
    - Time in window (0.20)
    - Duration accuracy (0.15)
    - Attendee inclusion (0.15)
    - No conflicts (0.05)
    
    Deterministic: Same meeting always gets same score
    """

    def __init__(self):
        super().__init__("MeetingGrader")
        self.last_feedback = ""

    def evaluate(self, state: APEXEnvState, task_data: Dict[str, Any]) -> float:
        """
        Evaluate meeting task.
        
        task_data should contain:
        - expected_date: datetime
        - expected_time_window: tuple (start_hour, end_hour)
        - expected_attendee_ids: List[int]
        - expected_duration: int (minutes)
        - expected_meeting_type: str
        - tolerance_minutes: int (for duration match, default 15)
        """
        score = 0.0
        details = {}
        
        # Check if meeting was scheduled
        if not state.meetings:
            self.last_feedback = "No meeting scheduled"
            self._record_evaluation(0.0, {"status": "no_meeting"})
            return 0.0
        
        # Get last scheduled meeting
        meeting = list(state.meetings.values())[-1]
        details["meeting_id"] = meeting.meeting_id
        
        # 1. MEETING SCHEDULED (0.20)
        scheduled_score = 0.20
        score += scheduled_score
        details["scheduled_score"] = scheduled_score
        
        # 2. DATE CORRECTNESS (0.25)
        expected_date = task_data.get("expected_date")
        if expected_date:
            date_match, date_score = self._evaluate_date(
                meeting.scheduled_time,
                expected_date,
            )
            score += date_score
            details["date_score"] = date_score
            details["date_match"] = date_match
        else:
            details["date_score"] = 0.0
        
        # 3. TIME IN WINDOW (0.20)
        time_window = task_data.get("expected_time_window", (9, 17))
        window_match, window_score = self._evaluate_time_window(
            meeting.scheduled_time,
            time_window,
            meeting.duration_minutes,
        )
        score += window_score
        details["window_score"] = window_score
        details["window_match"] = window_match
        
        # 4. DURATION ACCURACY (0.15)
        expected_duration = task_data.get("expected_duration", 60)
        tolerance = task_data.get("tolerance_minutes", 15)
        duration_score = self._evaluate_duration(
            meeting.duration_minutes,
            expected_duration,
            tolerance,
        )
        score += duration_score
        details["duration_score"] = duration_score
        details["expected_duration"] = expected_duration
        details["actual_duration"] = meeting.duration_minutes
        
        # 5. ATTENDEE INCLUSION (0.15)
        expected_attendees = task_data.get("expected_attendee_ids", [])
        attendee_score = self._evaluate_attendees(
            meeting.attendee_ids,
            expected_attendees,
        )
        score += attendee_score
        details["attendee_score"] = attendee_score
        details["expected_attendees"] = len(expected_attendees)
        details["actual_attendees"] = len(meeting.attendee_ids)
        
        # 6. NO CONFLICTS (0.05)
        conflicts_score = self._evaluate_conflicts(state, meeting)
        score += conflicts_score
        details["conflicts_score"] = conflicts_score
        
        # Record evaluation
        final_score = min(1.0, score)
        details["total_score"] = final_score
        self._record_evaluation(final_score, details)
        
        # Generate feedback
        self._generate_feedback(details)
        
        return final_score

    def _evaluate_date(self, actual_time: datetime, expected_date: datetime) -> tuple:
        """
        Check if meeting is on expected date.
        
        Returns: (match: bool, score: float)
        """
        actual_date = actual_time.date()
        expected = expected_date.date()
        
        if actual_date == expected:
            return (True, 0.25)
        
        # Adjacent days acceptable (partial credit)
        diff = abs((actual_date - expected).days)
        if diff == 1:
            return (False, 0.12)
        
        return (False, 0.0)

    def _evaluate_time_window(self, meeting_time: datetime, window: tuple, 
                            duration: int) -> tuple:
        """
        Check if meeting time falls within expected window.
        
        Returns: (match: bool, score: float)
        """
        start_hour, end_hour = window
        meeting_hour = meeting_time.hour
        meeting_end_hour = meeting_hour + (meeting_time.minute + duration) // 60
        
        # Perfect fit: starts and ends within window
        if (start_hour <= meeting_hour and meeting_end_hour <= end_hour):
            return (True, 0.20)
        
        # Partial fit: starts within window
        if (start_hour <= meeting_hour < end_hour):
            return (True, 0.15)
        
        # Off by one hour
        if abs(meeting_hour - start_hour) == 1:
            return (False, 0.10)
        
        return (False, 0.0)

    def _evaluate_duration(self, actual: int, expected: int, 
                          tolerance: int) -> float:
        """
        Check if meeting duration matches expected.
        
        Returns: score in [0.0, 0.15]
        """
        diff = abs(actual - expected)
        
        # Exact match
        if diff == 0:
            return 0.15
        
        # Within tolerance
        if diff <= tolerance:
            return 0.15 * (1.0 - diff / tolerance)
        
        return 0.0

    def _evaluate_attendees(self, actual_ids: list, expected_ids: list) -> float:
        """
        Check if attendees match.
        
        Returns: score in [0.0, 0.15]
        """
        if not expected_ids:
            return 0.08  # Base credit for scheduling
        
        actual_set = set(actual_ids)
        expected_set = set(expected_ids)
        
        # All required attendees present
        if expected_set.issubset(actual_set):
            return 0.15
        
        # Some attendees present
        if actual_set & expected_set:
            overlap = len(actual_set & expected_set)
            return 0.15 * (overlap / len(expected_set))
        
        return 0.0

    def _evaluate_conflicts(self, state: APEXEnvState, meeting) -> float:
        """
        Check if meeting has conflicts with other meetings.
        
        Returns: score in [0.0, 0.05]
        """
        conflicts = state.find_meeting_conflicts(meeting)
        
        if not conflicts:
            return 0.05
        
        return 0.0

    def _generate_feedback(self, details: Dict[str, Any]) -> None:
        """Generate human-readable feedback"""
        score = details.get("total_score", 0.0)
        
        feedback = f"Meeting Evaluation Score: {score:.2f}\n"
        feedback += f"  Scheduled: {details.get('scheduled_score', 0.0):.2f}/0.20\n"
        feedback += f"  Date: {details.get('date_score', 0.0):.2f}/0.25\n"
        feedback += f"  Time Window: {details.get('window_score', 0.0):.2f}/0.20\n"
        feedback += f"  Duration: {details.get('duration_score', 0.0):.2f}/0.15\n"
        feedback += f"  Attendees: {details.get('attendee_score', 0.0):.2f}/0.15\n"
        feedback += f"  Conflicts: {details.get('conflicts_score', 0.0):.2f}/0.05\n"
        
        if score >= 0.85:
            feedback += "\n✓ Excellent meeting scheduling"
        elif score >= 0.70:
            feedback += "\n✓ Good meeting scheduling"
        elif score >= 0.50:
            feedback += "\n⚠ Acceptable meeting scheduling"
        else:
            feedback += "\n✗ Needs improvement"
        
        self.last_feedback = feedback

    def get_detailed_feedback(self) -> str:
        """Return last evaluation feedback"""
        return self.last_feedback
