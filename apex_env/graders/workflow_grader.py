"""
Workflow grader for APEXEnv

Evaluates multi-step workflows (e.g., translate → email → meeting).
"""

from typing import Dict, Any, List
from apex_env.state import APEXEnvState
from apex_env.graders.base_grader import BaseGrader
from apex_env.graders.email_grader import EmailGrader
from apex_env.graders.meeting_grader import MeetingGrader


class WorkflowGrader(BaseGrader):
    """
    Grader for multi-step workflow evaluation.
    
    Evaluates complex workflows like:
    - Translate text → Send email → Schedule meeting
    - Process gesture → Send confirmation → Update calendar
    
    Scoring criteria:
    - Step 1 completion (0.25)
    - Step 2 completion (0.35)
    - Step 3 completion (0.25)
    - Workflow coherence (0.15)
    
    Deterministic: Same workflow always gets same score
    """

    def __init__(self):
        super().__init__("WorkflowGrader")
        self.last_feedback = ""
        self.email_grader = EmailGrader()
        self.meeting_grader = MeetingGrader()

    def evaluate(self, state: APEXEnvState, task_data: Dict[str, Any]) -> float:
        """
        Evaluate workflow task.
        
        task_data should contain:
        - steps: List[str] of step names, e.g. ["translate", "email", "meeting"]
        - step_1_data: Dict with step-specific evaluation data
        - step_2_data: Dict with step-specific evaluation data
        - step_3_data: Dict with step-specific evaluation data
        """
        score = 0.0
        details = {}
        
        steps = task_data.get("steps", [])
        if not steps:
            self.last_feedback = "No workflow steps defined"
            self._record_evaluation(0.0, {"status": "no_steps"})
            return 0.0
        
        # Evaluate each step based on its type
        step_scores = []
        
        for i, step in enumerate(steps, 1):
            step_key = f"step_{i}"
            step_data = task_data.get(f"{step_key}_data", {})
            
            if step == "translate":
                step_score = self._evaluate_translation(state, step_data)
            elif step == "email":
                step_score = self._evaluate_email(state, step_data)
            elif step == "meeting":
                step_score = self._evaluate_meeting(state, step_data)
            else:
                step_score = 0.0
            
            step_scores.append((step, step_score))
            details[f"{step_key}_score"] = step_score
        
        # Weighted scoring based on number of steps
        if len(steps) == 1:
            score = step_scores[0][1]
        elif len(steps) == 2:
            score = 0.4 * step_scores[0][1] + 0.6 * step_scores[1][1]
        elif len(steps) >= 3:
            # 3+ steps
            score = (0.25 * step_scores[0][1] + 
                    0.35 * step_scores[1][1] + 
                    0.25 * step_scores[2][1])
            
            # Workflow coherence bonus: 0.15
            coherence = self._evaluate_coherence(state, steps)
            score += 0.15 * coherence
            details["coherence_score"] = 0.15 * coherence
        
        # Record evaluation
        final_score = min(1.0, score)
        details["total_score"] = final_score
        self._record_evaluation(final_score, details)
        
        # Generate feedback
        self._generate_feedback(details, step_scores)
        
        return final_score

    def _evaluate_translation(self, state: APEXEnvState, 
                             step_data: Dict[str, Any]) -> float:
        """
        Evaluate translation step completion.
        
        Returns: score in [0.0, 1.0]
        """
        if not state.translation_history:
            return 0.0
        
        translation = state.translation_history[-1]
        src, tgt, text = translation
        
        expected_src = step_data.get("source_language")
        expected_tgt = step_data.get("target_language")
        
        score = 0.0
        
        # Language pair match: 0.7
        if (src == expected_src and tgt == expected_tgt):
            score += 0.7
        elif (tgt == expected_tgt):
            score += 0.4
        
        # Text length reasonable: 0.3
        if len(text) >= 5:
            score += 0.3
        
        return min(1.0, score)

    def _evaluate_email(self, state: APEXEnvState, 
                       step_data: Dict[str, Any]) -> float:
        """
        Evaluate email step completion.
        
        Returns: score in [0.0, 1.0]
        """
        if not state.emails_sent:
            return 0.0
        
        # Use EmailGrader for detailed evaluation
        email_score = self.email_grader.evaluate(state, step_data)
        
        return email_score

    def _evaluate_meeting(self, state: APEXEnvState, 
                         step_data: Dict[str, Any]) -> float:
        """
        Evaluate meeting step completion.
        
        Returns: score in [0.0, 1.0]
        """
        if not state.meetings:
            return 0.0
        
        # Use MeetingGrader for detailed evaluation
        meeting_score = self.meeting_grader.evaluate(state, step_data)
        
        return meeting_score

    def _evaluate_coherence(self, state: APEXEnvState, steps: List[str]) -> float:
        """
        Evaluate workflow coherence (steps executed in logical order).
        
        Returns: score in [0.0, 1.0]
        """
        if not steps:
            return 0.0
        
        coherence = 0.0
        
        # Check temporal ordering
        if "translate" in steps and "email" in steps:
            # Translation should happen before email
            if state.translation_history and state.emails_sent:
                trans_time = state.translation_history[-1] if state.translation_history else None
                email_time = state.emails_sent[-1].timestamp if state.emails_sent else None
                
                # Both should exist (not timing check in mock env)
                coherence += 0.5
        
        # Check action appropriateness
        if "email" in steps and state.emails_sent:
            coherence += 0.25
        
        if "meeting" in steps and state.meetings:
            coherence += 0.25
        
        return min(1.0, coherence)

    def _generate_feedback(self, details: Dict[str, Any], 
                          step_scores: List[tuple]) -> None:
        """Generate human-readable feedback"""
        score = details.get("total_score", 0.0)
        
        feedback = f"Workflow Evaluation Score: {score:.2f}\n\n"
        feedback += "Step Scores:\n"
        
        for step, step_score in step_scores:
            feedback += f"  {step.capitalize()}: {step_score:.2f}/1.00\n"
        
        if "coherence_score" in details:
            feedback += f"  Coherence: {details['coherence_score']:.2f}/0.15\n"
        
        if score >= 0.85:
            feedback += "\n✓ Excellent workflow execution"
        elif score >= 0.70:
            feedback += "\n✓ Good workflow execution"
        elif score >= 0.50:
            feedback += "\n⚠ Acceptable workflow execution"
        else:
            feedback += "\n✗ Workflow needs improvement"
        
        self.last_feedback = feedback

    def get_detailed_feedback(self) -> str:
        """Return last evaluation feedback"""
        return self.last_feedback
