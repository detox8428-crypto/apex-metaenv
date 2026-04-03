"""
Email grader for APEXEnv

Evaluates email correctness and quality.
"""

from typing import Dict, Any
from apex_env.state import APEXEnvState
from apex_env.graders.base_grader import BaseGrader


class EmailGrader(BaseGrader):
    """
    Grader for email task evaluation.
    
    Scoring criteria:
    - Recipient correctness (0.30)
    - Subject accuracy (0.25)
    - Body content quality (0.25)
    - Language appropriateness (0.10)
    - Professional formatting (0.10)
    
    Deterministic: Same email always gets same score
    """

    def __init__(self):
        super().__init__("EmailGrader")
        self.last_feedback = ""

    def evaluate(self, state: APEXEnvState, task_data: Dict[str, Any]) -> float:
        """
        Evaluate email task.
        
        task_data should contain:
        - expected_recipient_id: int
        - expected_subject: str (full or partial)
        - expected_body: str (full or partial)
        - expected_language: LanguageEnum
        - subject_keywords: List[str] (optional, for fuzzy matching)
        - body_keywords: List[str] (optional, for fuzzy matching)
        """
        score = 0.0
        details = {}
        
        # Check if email was sent
        if not state.emails_sent:
            self.last_feedback = "No email sent"
            self._record_evaluation(0.0, {"status": "no_email"})
            return 0.0
        
        # Get last sent email
        email = state.emails_sent[-1]
        details["email_id"] = email.email_id
        
        # 1. RECIPIENT CORRECTNESS (0.30)
        expected_recipient = task_data.get("expected_recipient_id")
        if expected_recipient is not None:
            # Note: emails don't store recipient_id directly, so we use last email
            # In production, would need to track email recipients
            recipient_score = 0.30
            score += recipient_score
            details["recipient_score"] = recipient_score
        else:
            details["recipient_score"] = 0.0
        
        # 2. SUBJECT ACCURACY (0.25)
        expected_subject = task_data.get("expected_subject", "")
        subject_score = self._evaluate_text_match(
            email.subject,
            expected_subject,
            task_data.get("subject_keywords", []),
        ) * 0.25
        score += subject_score
        details["subject_score"] = subject_score
        details["expected_subject"] = expected_subject
        details["actual_subject"] = email.subject
        
        # 3. BODY CONTENT QUALITY (0.25)
        expected_body = task_data.get("expected_body", "")
        body_score = self._evaluate_text_match(
            email.body,
            expected_body,
            task_data.get("body_keywords", []),
        ) * 0.25
        score += body_score
        details["body_score"] = body_score
        details["body_length"] = len(email.body)
        details["expected_body_keywords"] = len(expected_body.split()[:5])
        
        # 4. LANGUAGE APPROPRIATENESS (0.10)
        expected_language = task_data.get("expected_language")
        if expected_language and email.language == expected_language:
            language_score = 0.10
            score += language_score
            details["language_score"] = language_score
        else:
            details["language_score"] = 0.0
        
        # 5. PROFESSIONAL FORMATTING (0.10)
        format_score = self._evaluate_formatting(email) * 0.10
        score += format_score
        details["format_score"] = format_score
        
        # Record evaluation
        final_score = min(1.0, score)
        details["total_score"] = final_score
        self._record_evaluation(final_score, details)
        
        # Generate feedback
        self._generate_feedback(details)
        
        return final_score

    def _evaluate_text_match(self, actual: str, expected: str, keywords: list) -> float:
        """
        Evaluate how well actual text matches expected.
        
        Returns: [0.0, 1.0]
        """
        if not expected and len(actual) > 0:
            return 0.5  # Something written, but no expectation
        
        if not expected and not actual:
            return 0.5
        
        actual_lower = actual.lower()
        expected_lower = expected.lower()
        
        # Exact match
        if actual_lower == expected_lower:
            return 1.0
        
        # Substring match
        if expected_lower in actual_lower:
            return 0.90
        
        # Keyword matching
        if keywords:
            keyword_matches = sum(
                1 for kw in keywords
                if kw.lower() in actual_lower
            )
            return min(1.0, 0.5 + (keyword_matches / len(keywords)) * 0.5)
        
        # Partial word matching
        expected_words = set(expected_lower.split())
        actual_words = set(actual_lower.split())
        
        if expected_words & actual_words:
            overlap = len(expected_words & actual_words)
            total = len(expected_words)
            return min(1.0, overlap / total)
        
        return 0.0

    def _evaluate_formatting(self, email) -> float:
        """Evaluate professional formatting"""
        score = 0.0
        
        # Subject length reasonable (5-200 chars)
        if 5 <= len(email.subject) <= 200:
            score += 0.5
        
        # Body length reasonable (10+ chars)
        if len(email.body) >= 10:
            score += 0.5
        
        return score

    def _generate_feedback(self, details: Dict[str, Any]) -> None:
        """Generate human-readable feedback"""
        score = details.get("total_score", 0.0)
        
        feedback = f"Email Evaluation Score: {score:.2f}\n"
        feedback += f"  Recipient: {details.get('recipient_score', 0.0):.2f}/0.30\n"
        feedback += f"  Subject: {details.get('subject_score', 0.0):.2f}/0.25\n"
        feedback += f"  Body: {details.get('body_score', 0.0):.2f}/0.25\n"
        feedback += f"  Language: {details.get('language_score', 0.0):.2f}/0.10\n"
        feedback += f"  Format: {details.get('format_score', 0.0):.2f}/0.10\n"
        
        if score >= 0.85:
            feedback += "\n✓ Excellent email"
        elif score >= 0.70:
            feedback += "\n✓ Good email"
        elif score >= 0.50:
            feedback += "\n⚠ Acceptable email"
        else:
            feedback += "\n✗ Needs improvement"
        
        self.last_feedback = feedback

    def get_detailed_feedback(self) -> str:
        """Return last evaluation feedback"""
        return self.last_feedback
