"""
Core APEXEnv environment implementation following OpenEnv specification
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
from enum import Enum
import math

from apex_env.models import (
    Action,
    EmailAction,
    MeetingAction,
    TranslationAction,
    GestureAction,
    NoOpAction,
    WhatsAppAction,
    SearchAction,
    SummarizeAction,
    CodeGenAction,
    CommandExecAction,
    DebugAction,
    Observation,
    Reward,
    RewardBreakdown,
    ActionResult,
    StepInfo,
    EnvironmentConfig,
    Email,
    Meeting,
    EmailStatus,
    CalendarStatus,
    LanguageContext,
    GestureContext,
    SystemState,
    TimeWindow,
    LanguageEnum,
    MeetingTypeEnum,
    PriorityEnum,
    GestureEnum,
)
from apex_env.state import APEXEnvState, Contact, Task
from apex_env.email_provider import email_manager
from apex_env.whatsapp_integration import whatsapp_manager
from apex_env.search_provider import search_manager
from apex_env.content_summarizer import summarizer_manager
from apex_env.code_generator import code_generator_manager
from apex_env.command_executor import command_executor_manager
from apex_env.vscode_debugger import vscode_debugger_manager


class APEXEnv:
    """
    Autonomous Productivity EXecutor (APEX) Environment
    
    OpenEnv-compliant environment for training productivity agents.
    Supports: email, calendar, multilingual processing, gesture recognition.
    """

    def __init__(self, config: Optional[EnvironmentConfig] = None):
        """Initialize environment"""
        self.config = config or EnvironmentConfig()
        self.state = APEXEnvState()
        self._episode_return = 0.0
        self._steps_taken = 0
        self._initialize_contacts()
        
        # Random seed
        if self.config.seed is not None:
            random.seed(self.config.seed)

    def _initialize_contacts(self) -> None:
        """Initialize contact database with synthetic contacts"""
        names = [
            "Alice J.", "Bob S.", "Charlie H.", "Diana P.", "Eve M.",
            "Frank L.", "Grace K.", "Henry B.", "Iris T.", "Jack D."
        ]
        
        for i in range(min(100, self.config.num_contacts)):  # Create first 100 contacts
            contact = Contact(
                contact_id=i,
                name=names[i % len(names)] if i < len(names) else f"Contact {i}",
                email=f"contact{i}@example.com",
                languages=[LanguageEnum.EN, LanguageEnum.ES] if i % 3 == 0 else [LanguageEnum.EN],
            )
            self.state.add_contact(contact)

    def reset(self) -> Observation:
        """
        Reset environment to initial state.
        Returns initial observation.
        """
        self.state.reset()
        self._episode_return = 0.0
        self._steps_taken = 0
        
        return self._get_observation()

    def _validate_action(self, action: Action) -> Tuple[bool, Optional[str]]:
        """Validate action against environment constraints"""
        if isinstance(action, EmailAction):
            # Validate recipient exists
            if not self.state.get_contact(action.recipient_id):
                return False, f"Recipient ID {action.recipient_id} not found"
            
            # Validate subject and body not empty
            if not action.subject.strip() or not action.body.strip():
                return False, "Subject or body is empty"
            
            # Validate CC/BCC exist
            for cc_id in action.cc_ids:
                if not self.state.get_contact(cc_id):
                    return False, f"CC recipient {cc_id} not found"
            
            return True, None

        elif isinstance(action, MeetingAction):
            # Validate attendees exist
            for attendee_id in action.attendee_ids:
                if not self.state.get_contact(attendee_id):
                    return False, f"Attendee {attendee_id} not found"
            
            # Validate scheduled time is in the future
            if action.scheduled_time <= datetime.utcnow():
                return False, "Meeting time must be in the future"
            
            return True, None

        elif isinstance(action, TranslationAction):
            # Validate text not empty
            if not action.text.strip():
                return False, "Translation text is empty"
            
            # Validate languages differ (Pydantic handles this, but double-check)
            if action.source_language == action.target_language:
                return False, "Source and target languages must differ"
            
            return True, None

        elif isinstance(action, GestureAction):
            # Validate intensity in range
            if not (0.0 <= action.intensity <= 1.0):
                return False, "Gesture intensity must be between 0.0 and 1.0"
            
            return True, None

        elif isinstance(action, NoOpAction):
            return True, None

        return False, "Unknown action type"

    def _process_email_action(self, action: EmailAction) -> ActionResult:
        """Process email sending action"""
        start_time = datetime.utcnow()
        
        try:
            # Simulate SMTP delay
            contact = self.state.get_contact(action.recipient_id)
            
            # Create email record
            email = Email(
                email_id=len(self.state.emails_sent) + len(self.state.emails_pending),
                sender_id=0,  # Agent is sender 0
                subject=action.subject,
                body=action.body,
                language=action.language,
                timestamp=datetime.utcnow(),
                read=False,
            )
            
            # Add to pending (simulate sending)
            success, error = self.state.add_email(email, status="sent")
            
            if not success:
                self.state.record_error(error)
                return ActionResult(
                    action_type="email",
                    success=False,
                    message=error,
                    error_code="EMAIL_SEND_FAILED",
                )
            
            # Send real email if requested and configured
            real_email_sent = False
            if action.send_real and email_manager.enabled:
                try:
                    real_email_sent = email_manager.send_email(
                        action.recipient_id,
                        action.subject,
                        action.body
                    )
                    if real_email_sent:
                        self.logger.info(f"Real email sent to contact {action.recipient_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to send real email: {str(e)}")
                    real_email_sent = False
            
            self.state.record_action("email", True)
            
            return ActionResult(
                action_type="email",
                success=True,
                message=f"Email sent to {contact.name}",
                details={
                    "recipient": contact.email,
                    "subject": action.subject,
                    "language": action.language.value,
                    "real_email_sent": real_email_sent,
                    "mode": "real" if real_email_sent else "simulated",
                }
            )
        
        except Exception as e:
            self.state.record_error(str(e))
            return ActionResult(
                action_type="email",
                success=False,
                message=f"Email failed: {str(e)}",
                error_code="EMAIL_EXCEPTION",
            )

    def _process_meeting_action(self, action: MeetingAction) -> ActionResult:
        """Process meeting scheduling action"""
        try:
            # Create meeting record
            meeting = Meeting(
                meeting_id=len(self.state.meetings),
                title=action.title,
                attendee_ids=action.attendee_ids,
                scheduled_time=action.scheduled_time,
                duration_minutes=action.duration_minutes,
                meeting_type=action.meeting_type,
                location=action.location,
                created_at=datetime.utcnow(),
            )
            
            # Check for conflicts
            success, error = self.state.add_meeting(meeting)
            
            if not success:
                self.state.record_error(error)
                return ActionResult(
                    action_type="meeting",
                    success=False,
                    message=error,
                    error_code="MEETING_CONFLICT",
                )
            
            self.state.record_action("meeting", True)
            
            attendee_names = [
                self.state.get_contact(aid).name
                for aid in action.attendee_ids[:3]
            ]
            
            return ActionResult(
                action_type="meeting",
                success=True,
                message=f"Meeting scheduled with {', '.join(attendee_names)}",
                details={
                    "meeting_id": meeting.meeting_id,
                    "title": action.title,
                    "attendees": len(action.attendee_ids),
                    "time": action.scheduled_time.isoformat(),
                }
            )
        
        except Exception as e:
            self.state.record_error(str(e))
            return ActionResult(
                action_type="meeting",
                success=False,
                message=f"Meeting failed: {str(e)}",
                error_code="MEETING_EXCEPTION",
            )

    def _process_translation_action(self, action: TranslationAction) -> ActionResult:
        """
        Process translation action with advanced features:
        - Language detection and confidence scoring
        - Language family and character set awareness
        - Quality adjustment based on language pair difficulty
        - Fallback chain support
        """
        try:
            # Language family and difficulty mapping
            language_data = {
                LanguageEnum.EN: {"family": "Indo-European", "charset": "Latin", "tier": 0},
                LanguageEnum.ES: {"family": "Indo-European", "charset": "Latin", "tier": 0},
                LanguageEnum.FR: {"family": "Indo-European", "charset": "Latin", "tier": 0},
                LanguageEnum.DE: {"family": "Indo-European", "charset": "Latin", "tier": 0},
                LanguageEnum.ZH: {"family": "Sino-Tibetan", "charset": "CJK", "tier": 2},
                LanguageEnum.JA: {"family": "Japonic", "charset": "CJK", "tier": 2},
            }
            
            # Get language information
            src_data = language_data.get(action.source_language, {"family": "Unknown", "charset": "Unknown", "tier": 1})
            tgt_data = language_data.get(action.target_language, {"family": "Unknown", "charset": "Unknown", "tier": 1})
            
            # Calculate translation quality based on language pair difficulty
            base_quality = 0.85
            
            # Difficulty adjustment: same family easier, different tier harder
            if src_data["family"] == tgt_data["family"]:
                difficulty_penalty = 0.0  # Same family = easier
            elif abs(src_data["tier"] - tgt_data["tier"]) > 1:
                difficulty_penalty = 0.15  # Different families, different tiers
            else:
                difficulty_penalty = 0.10  # Different families
            
            # Character set complexity adjustment
            if src_data["charset"] == tgt_data["charset"]:
                charset_penalty = 0.0  # Same character set
            else:
                charset_penalty = 0.05  # Different character sets
            
            # Calculate final quality
            quality_score = base_quality - difficulty_penalty - charset_penalty + random.random() * 0.15
            quality_score = max(0.5, min(1.0, quality_score))  # Clamp to [0.5, 1.0]
            
            # Simple language detection based on text characteristics
            detected_charset = self._detect_charset(action.text)
            confidence = self._calculate_language_confidence(
                action.source_language,
                detected_charset,
                action.text
            )
            
            # Build fallback chain for unavailable translations
            fallback_chain = self._build_fallback_chain(
                action.source_language,
                action.target_language
            )
            
            # Record translation
            self.state.translation_history.append((
                action.source_language,
                action.target_language,
                action.text,
            ))
            
            self.state.detected_language = action.source_language
            self.state.language_confidence = quality_score
            
            self.state.record_action("translation", True)
            
            return ActionResult(
                action_type="translation",
                success=True,
                message=f"Translation processed: {action.source_language.value} → {action.target_language.value}",
                details={
                    "source": action.source_language.value,
                    "target": action.target_language.value,
                    "quality": round(quality_score, 2),
                    "text_length": len(action.text),
                    "source_family": src_data["family"],
                    "target_family": tgt_data["family"],
                    "charset_conversion": f"{src_data['charset']} → {tgt_data['charset']}",
                    "detected_charset": detected_charset,
                    "language_confidence": round(confidence, 2),
                    "fallback_chain": [lang.value for lang in fallback_chain],
                }
            )
        
        except Exception as e:
            self.state.record_error(str(e))
            return ActionResult(
                action_type="translation",
                success=False,
                message=f"Translation failed: {str(e)}",
                error_code="TRANSLATION_EXCEPTION",
            )
    
    def _detect_charset(self, text: str) -> str:
        """Simple character set detection based on Unicode ranges"""
        if not text:
            return "ASCII"
        
        # Check for CJK characters
        if any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' for c in text):
            return "CJK"
        
        # Check for Cyrillic
        if any('\u0400' <= c <= '\u04ff' for c in text):
            return "Cyrillic"
        
        # Check for Arabic
        if any('\u0600' <= c <= '\u06ff' for c in text):
            return "Arabic"
        
        # Default to Latin
        return "Latin"
    
    def _calculate_language_confidence(self, language: LanguageEnum, charset: str, text: str) -> float:
        """Calculate confidence that detected language matches text"""
        # Base confidence
        confidence = 0.7
        
        # Boost based on text length (longer text = more confident)
        text_length_bonus = min(0.2, len(text) / 500.0)
        confidence += text_length_bonus
        
        # Adjust based on charset matching
        language_charset_map = {
            LanguageEnum.EN: "Latin",
            LanguageEnum.ES: "Latin",
            LanguageEnum.FR: "Latin",
            LanguageEnum.DE: "Latin",
            LanguageEnum.ZH: "CJK",
            LanguageEnum.JA: "CJK",
        }
        
        expected_charset = language_charset_map.get(language, "Latin")
        if charset == expected_charset:
            confidence += 0.15
        else:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _build_fallback_chain(self, source: LanguageEnum, target: LanguageEnum) -> list:
        """Build fallback chain for language pair translation"""
        # Direct translation fallback: if unavailable, use intermediate language
        fallback_map = {
            (LanguageEnum.ZH, LanguageEnum.JA): [LanguageEnum.EN],  # Via English
            (LanguageEnum.JA, LanguageEnum.ZH): [LanguageEnum.EN],  # Via English
            (LanguageEnum.DE, LanguageEnum.ES): [LanguageEnum.EN, LanguageEnum.FR],  # Via EN or FR
            (LanguageEnum.ES, LanguageEnum.DE): [LanguageEnum.EN, LanguageEnum.FR],  # Via EN or FR
        }
        
        return fallback_map.get((source, target), [LanguageEnum.EN])
    
    def _get_language_family(self, language: LanguageEnum) -> str:
        """Get language family for a given language"""
        language_families = {
            LanguageEnum.EN: "Indo-European",
            LanguageEnum.ES: "Indo-European",
            LanguageEnum.FR: "Indo-European",
            LanguageEnum.DE: "Indo-European",
            LanguageEnum.ZH: "Sino-Tibetan",
            LanguageEnum.JA: "Japonic",
        }
        return language_families.get(language, "Unknown")

    def _process_gesture_action(self, action: GestureAction) -> ActionResult:
        """
        Process gesture recognition action with advanced features:
        - Realistic gesture-to-action mapping
        - Intensity-based interpretation
        - Gesture sequence recognition
        - Context-aware suggestions
        """
        try:
            # Record gesture with intensity
            self.state.gesture_history.append(action.gesture_code)
            self.state.last_gesture = action.gesture_code
            
            # Advanced gesture mapping with context and intensity awareness
            gesture_map = {
                # Basic navigation gestures
                GestureEnum.SWIPE_RIGHT: {
                    "actions": ["Back", "Previous", "Undo"],
                    "intensity_threshold": 0.4,
                    "confidence": 0.95,
                },
                GestureEnum.SWIPE_LEFT: {
                    "actions": ["Forward", "Next", "Redo"],
                    "intensity_threshold": 0.4,
                    "confidence": 0.95,
                },
                GestureEnum.SWIPE_UP: {
                    "actions": ["Scroll up", "Expand", "Maximize"],
                    "intensity_threshold": 0.3,
                    "confidence": 0.92,
                },
                GestureEnum.SWIPE_DOWN: {
                    "actions": ["Scroll down", "Collapse", "Minimize"],
                    "intensity_threshold": 0.3,
                    "confidence": 0.92,
                },
                
                # Selection and confirmation gestures
                GestureEnum.DOUBLE_TAP: {
                    "actions": ["Confirm", "Execute", "Open"],
                    "intensity_threshold": 0.2,
                    "confidence": 0.98,
                },
                GestureEnum.LONG_PRESS: {
                    "actions": ["Show options", "Context menu", "Details"],
                    "intensity_threshold": 0.6,
                    "confidence": 0.90,
                },
                
                # Zoom and scale gestures
                GestureEnum.PINCH_ZOOM: {
                    "actions": ["Zoom in/out", "Scale", "Adjust"],
                    "intensity_threshold": 0.3,
                    "confidence": 0.88,
                },
                
                # Advanced gestures
                GestureEnum.TWO_FINGER_TAP: {
                    "actions": ["Right-click equivalent", "Secondary action"],
                    "intensity_threshold": 0.4,
                    "confidence": 0.85,
                },
                GestureEnum.THREE_FINGER_SWIPE: {
                    "actions": ["App switcher", "Multitask view", "System menu"],
                    "intensity_threshold": 0.5,
                    "confidence": 0.80,
                },
                GestureEnum.ROTATION: {
                    "actions": ["Rotate view", "Change orientation", "Reorder"],
                    "intensity_threshold": 0.3,
                    "confidence": 0.87,
                },
                GestureEnum.HOLD_AND_DRAG: {
                    "actions": ["Move", "Reorder", "Transfer", "Drag-drop"],
                    "intensity_threshold": 0.4,
                    "confidence": 0.92,
                },
                
                # Voice gesture
                GestureEnum.VOICE_COMMAND: {
                    "actions": ["Process voice input", "Voice control"],
                    "intensity_threshold": 0.1,
                    "confidence": 0.75,
                },
            }
            
            # Get gesture mapping
            gesture_info = gesture_map.get(
                action.gesture_code,
                {"actions": ["Unknown action"], "intensity_threshold": 0.5, "confidence": 0.5}
            )
            
            # Determine action based on intensity
            intensity = action.intensity
            intensity_level = "light" if intensity < 0.4 else "normal" if intensity < 0.7 else "strong"
            
            # Select appropriate action based on intensity
            actions = gesture_info["actions"]
            if intensity_level == "light" and len(actions) > 1:
                suggested_action = actions[0]
                confidence = gesture_info["confidence"] * 0.9  # Slightly lower confidence
            elif intensity_level == "strong" and len(actions) > 1:
                suggested_action = actions[-1]  # Use last action for strong gestures
                confidence = min(1.0, gesture_info["confidence"] * 1.05)
            else:
                suggested_action = actions[0] if actions else "Unknown"
                confidence = gesture_info["confidence"]
            
            # Check for gesture sequences (multi-gesture patterns)
            gesture_sequence = None
            contextual_interpretation = None
            if len(self.state.gesture_history) >= 2:
                recent_gestures = self.state.gesture_history[-2:]
                gesture_sequence = recent_gestures
                
                # Recognize common gesture combinations
                if (recent_gestures[0] == GestureEnum.SWIPE_RIGHT and 
                    recent_gestures[1] == GestureEnum.DOUBLE_TAP):
                    contextual_interpretation = "Quick navigate and confirm"
                elif (recent_gestures[0] == GestureEnum.LONG_PRESS and 
                      recent_gestures[1] == GestureEnum.SWIPE_LEFT):
                    contextual_interpretation = "Select and delete"
                elif (recent_gestures[0] == GestureEnum.PINCH_ZOOM and 
                      recent_gestures[1] == GestureEnum.HOLD_AND_DRAG):
                    contextual_interpretation = "Scale and move"
            
            self.state.record_action("gesture", True)
            
            # Build detailed result
            return ActionResult(
                action_type="gesture",
                success=True,
                message=f"Gesture recognized: {action.gesture_code.value} ({intensity_level})",
                details={
                    "gesture": action.gesture_code.value,
                    "intensity": action.intensity,
                    "intensity_level": intensity_level,
                    "suggested_action": suggested_action,
                    "contextual_interpretation": contextual_interpretation,
                    "gesture_sequence": [g.value for g in (gesture_sequence or [])],
                    "confidence": round(confidence, 2),
                }
            )
        
        except Exception as e:
            self.state.record_error(str(e))
            return ActionResult(
                action_type="gesture",
                success=False,
                message=f"Gesture processing failed: {str(e)}",
                error_code="GESTURE_EXCEPTION",
            )

    def _process_noop_action(self, action: NoOpAction) -> ActionResult:
        """Process no-op action"""
        self.state.record_action("noop", True)
        return ActionResult(
            action_type="noop",
            success=True,
            message="No operation performed",
        )

    def _process_whatsapp_action(self, action: WhatsAppAction) -> ActionResult:
        """Process WhatsApp message action"""
        try:
            if not whatsapp_manager.enabled:
                return ActionResult(
                    action_type="whatsapp",
                    success=False,
                    message="WhatsApp not configured",
                    error_code="WHATSAPP_NOT_CONFIGURED",
                )
            
            # Send message
            if action.media_url:
                result = whatsapp_manager.send_media(
                    action.phone_number,
                    action.media_url,
                    action.media_type or "image",
                    action.message
                )
            elif action.use_template:
                result = whatsapp_manager.send_template(
                    action.phone_number,
                    action.template_name or "hello_world",
                    action.template_params
                )
            else:
                result = whatsapp_manager.send_message(action.phone_number, action.message)
            
            self.state.record_action("whatsapp", result.get("success", False))
            
            return ActionResult(
                action_type="whatsapp",
                success=result.get("success", False),
                message=result.get("message_id", result.get("error", "Unknown error")),
                details={
                    "phone": action.phone_number,
                    "message_preview": action.message[:100],
                    "provider": result.get("provider", "unknown"),
                }
            )
        except Exception as e:
            self.state.record_action("whatsapp", False)
            return ActionResult(
                action_type="whatsapp",
                success=False,
                message=f"WhatsApp error: {str(e)}",
                error_code="WHATSAPP_ERROR",
            )
    
    def _process_search_action(self, action: SearchAction) -> ActionResult:
        """Process web search action"""
        try:
            # Perform search
            result = search_manager.search(
                action.query,
                action.num_results,
                action.provider
            )
            
            success = result.get("success", False)
            self.state.record_action("search", success)
            
            return ActionResult(
                action_type="search",
                success=success,
                message=f"Found {result.get('total', 0)} results" if success else result.get("error", "Search failed"),
                details={
                    "query": action.query,
                    "results_count": result.get("total", 0),
                    "provider": result.get("provider", "unknown"),
                    "top_result": result["results"][0]["url"] if result.get("results") else None,
                }
            )
        except Exception as e:
            self.state.record_action("search", False)
            return ActionResult(
                action_type="search",
                success=False,
                message=f"Search error: {str(e)}",
                error_code="SEARCH_ERROR",
            )
    
    def _process_summarize_action(self, action: SummarizeAction) -> ActionResult:
        """Process content summarization action"""
        try:
            # Summarize content
            result = summarizer_manager.summarize(action.content, action.style)
            
            success = result.get("success", False)
            self.state.record_action("summarize", success)
            
            return ActionResult(
                action_type="summarize",
                success=success,
                message=result.get("summary", result.get("error", "Summarization failed")) if success else result.get("error"),
                details={
                    "style": action.style,
                    "original_length": result.get("content_length", 0),
                    "tokens_used": result.get("tokens_used", 0),
                    "cost": result.get("cost", 0),
                }
            )
        except Exception as e:
            self.state.record_action("summarize", False)
            return ActionResult(
                action_type="summarize",
                success=False,
                message=f"Summarization error: {str(e)}",
                error_code="SUMMARIZE_ERROR",
            )
    
    def _process_code_gen_action(self, action: CodeGenAction) -> ActionResult:
        """Process code generation action"""
        try:
            # Dispatch based on task
            if action.task == "generate":
                result = code_generator_manager.generate(action.description, action.language, action.context)
            elif action.task == "fix":
                result = code_generator_manager.fix_bug(action.code or "", action.description, action.language)
            elif action.task == "refactor":
                result = code_generator_manager.refactor(action.code or "", action.language, action.context)
            elif action.task == "explain":
                result = code_generator_manager.explain(action.code or "", action.language)
            elif action.task == "test":
                result = code_generator_manager.generate_tests(action.code or "", action.language)
            else:
                result = {"success": False, "error": f"Unknown task: {action.task}"}
            
            success = result.get("success", False)
            self.state.record_action("code_gen", success)
            
            output_key = {
                "generate": "code",
                "fix": "fixed_code",
                "refactor": "refactored_code",
                "explain": "explanation",
                "test": "tests"
            }.get(action.task, "code")
            
            return ActionResult(
                action_type="code_gen",
                success=success,
                message=result.get(output_key, result.get("error", "Code generation failed")) if success else result.get("error"),
                details={
                    "task": action.task,
                    "language": action.language,
                    "tokens": result.get("tokens", 0),
                    "cost": result.get("cost", 0),
                }
            )
        except Exception as e:
            self.state.record_action("code_gen", False)
            return ActionResult(
                action_type="code_gen",
                success=False,
                message=f"Code generation error: {str(e)}",
                error_code="CODE_GEN_ERROR",
            )
    
    def _process_cmd_exec_action(self, action: CommandExecAction) -> ActionResult:
        """Process command execution action"""
        try:
            # Execute command
            result = command_executor_manager.execute(
                action.command,
                action.shell,
                action.require_confirmation,
                action.timeout_seconds
            )
            
            success = result.get("success", False)
            self.state.record_action("cmd_exec", success)
            
            return ActionResult(
                action_type="cmd_exec",
                success=success,
                message=result.get("stdout", result.get("error", "Command failed"))[:200] if success else result.get("error"),
                details={
                    "shell": action.shell,
                    "return_code": result.get("return_code"),
                    "execution_time": result.get("execution_time", 0),
                    "command_type": result.get("command_type"),
                    "requires_confirmation": result.get("requires_confirmation", False),
                }
            )
        except Exception as e:
            self.state.record_action("cmd_exec", False)
            return ActionResult(
                action_type="cmd_exec",
                success=False,
                message=f"Command execution error: {str(e)}",
                error_code="CMD_EXEC_ERROR",
            )
    
    def _process_debug_action(self, action: DebugAction) -> ActionResult:
        """Process debugging and error correction action"""
        try:
            if action.action == "analyze":
                result = vscode_debugger_manager.analyze_error(action.error_text, action.language)
            elif action.action == "correct":
                result = vscode_debugger_manager.get_correction(action.error_text, action.code, action.language)
            else:
                result = {"success": False, "error": f"Unknown debug action: {action.action}"}
            
            success = result.get("success", False)
            self.state.record_action("debug", success)
            
            output_key = {
                "analyze": "parsed_error",
                "correct": "correction"
            }.get(action.action, "result")
            
            return ActionResult(
                action_type="debug",
                success=success,
                message=str(result.get(output_key, result.get("error", "Debug failed")))[:200] if success else result.get("error"),
                details={
                    "language": action.language,
                    "action": action.action,
                    "error_type": result.get("parsed_error", {}).get("error_type") if action.action == "analyze" else result.get("error_type"),
                }
            )
        except Exception as e:
            self.state.record_action("debug", False)
            return ActionResult(
                action_type="debug",
                success=False,
                message=f"Debug error: {str(e)}",
                error_code="DEBUG_ERROR",
            )

    def _compute_reward(self, action_result: ActionResult) -> Tuple[float, RewardBreakdown]:
        """
        Compute reward with advanced shaping and granular components.
        
        Components:
        1. Action Success: Correctness of the action
        2. Task Progress: Completion progress
        3. Parameter Quality: Quality of action parameters
        4. Temporal Efficiency: Speed bonus
        5. Context Awareness: Action relevance
        6. Efficiency Penalty: Discourages repetition
        7. Error Penalty: Failed actions
        8. Language Accuracy: Multilingual handling
        9. Consistency Bonus: Coherent sequences
        10. State Stability: Avoid conflicts
        """
        import random
        
        # 1. ACTION SUCCESS: ±1.0 based on success
        action_success = 1.0 if action_result.success else -1.0
        
        # 2. TASK PROGRESS: [0.0, 1.0] based on completion
        task_progress = 0.0
        if self.state.current_task_id is not None:
            task_progress = self.state.get_task_progress(self.state.current_task_id)
            if action_result.success:
                self.state.mark_task_action_complete(
                    self.state.current_task_id,
                    action_result.action_type
                )
                task_progress = self.state.get_task_progress(self.state.current_task_id)
        
        # 3. PARAMETER QUALITY: [0.0, 1.0] based on action parameters
        parameter_quality = 0.0
        if action_result.success and action_result.details:
            # Bonus for detailed/well-formed parameters
            details = action_result.details
            param_count = len(details)
            completeness = min(1.0, param_count / 5.0)  # 5 params = max bonus
            parameter_quality = completeness * 0.5  # Up to 0.5 bonus
        
        # 4. TEMPORAL EFFICIENCY: Bonus for quick task completion
        temporal_efficiency = 0.0
        if self._steps_taken <= self.config.max_episode_steps * 0.3:  # Early completion
            temporal_efficiency = 0.1 * (1.0 - (self._steps_taken / (self.config.max_episode_steps * 0.3)))
        
        # 5. CONTEXT AWARENESS: Reward for actions relevant to current task
        context_awareness = 0.0
        if (self.state.current_task_id is not None and 
            action_result.action_type in ["email", "meeting", "translation"]):
            context_awareness = 0.15  # Bonus for task-relevant actions
        
        # 6. EFFICIENCY PENALTY: Discourage repeated actions
        efficiency_penalty = 0.0
        if len(self.state.action_history) >= 2:
            recent_actions = [a for a in self.state.action_history[-5:]]
            action_type = action_result.action_type
            recent_same = sum(1 for _, a, _ in recent_actions if a == action_type)
            if recent_same >= 3:
                efficiency_penalty = -0.15  # Penalty for repetition
            elif recent_same >= 2:
                efficiency_penalty = -0.05
        
        # 7. ERROR PENALTY: Failed actions
        error_penalty = 0.0
        if not action_result.success:
            error_penalty = -0.2  # Less severe than old system
        
        # 8. LANGUAGE ACCURACY: Multilingual handling bonus
        language_accuracy = 0.0
        if action_result.action_type == "translation":
            language_accuracy = self.state.language_confidence * 0.15
        elif action_result.action_type == "email":
            # Bonus for email in non-English context
            if self.state.detected_language != LanguageEnum.EN:
                language_accuracy = 0.2
            else:
                language_accuracy = 0.1
        elif action_result.action_type == "gesture":
            language_accuracy = 0.05  # Small bonus for gesture recognition
        
        # 9. CONSISTENCY BONUS: Reward for coherent action sequences
        consistency_bonus = 0.0
        if len(self.state.action_history) >= 3:
            recent_actions = [a for a in self.state.action_history[-3:]]
            action_types = [a for _, a, _ in recent_actions]
            # Coherence: similar actions or logical progression
            if action_types[-1] == action_result.action_type:
                consistency_bonus = 0.05  # Continuing same action type
            elif action_types[-2] != action_types[-1]:
                consistency_bonus = 0.03  # Logical action progression
        
        # 10. STATE STABILITY: Penalty for causing conflicts
        state_stability = 0.0
        if action_result.success:
            # Check if action caused any issues (errors in recent history)
            if len(self.state.error_history) > 0:
                state_stability = -0.1
        else:
            state_stability = -0.05
        
        # Build breakdown with all components
        breakdown = RewardBreakdown(
            action_success=action_success,
            task_progress=task_progress,
            parameter_quality=parameter_quality,
            temporal_efficiency=temporal_efficiency,
            context_awareness=context_awareness,
            efficiency_penalty=efficiency_penalty,
            error_penalty=error_penalty,
            language_accuracy=language_accuracy,
            consistency_bonus=consistency_bonus,
            state_stability=state_stability,
        )
        
        # Compute total reward as weighted sum of all components
        # Using importance-based weighting
        components = [
            (action_success, 0.25),          # Most important: did action work?
            (task_progress, 0.20),           # Second: task progress
            (parameter_quality, 0.10),       # Quality of parameters
            (temporal_efficiency, 0.08),     # Speed bonus
            (context_awareness, 0.08),       # Relevance
            (efficiency_penalty, 0.08),      # Avoid repetition
            (error_penalty, 0.05),          # Penalize errors
            (language_accuracy, 0.10),      # Multilingual handling
            (consistency_bonus, 0.04),      # Coherence
            (state_stability, 0.02),        # System health
        ]
        
        total = sum(comp * weight for comp, weight in components)
        total = max(-1.0, min(1.0, total))  # Clamp to [-1, 1]
        
        return total, breakdown

    def _get_observation(self) -> Observation:
        """Convert internal state to observation"""
        now = datetime.utcnow()
        
        # Email status
        email_status = EmailStatus(
            pending_count=len(self.state.emails_pending),
            inbox_count=len(self.state.emails_pending),
            sent_count=len(self.state.emails_sent),
            failed_count=len(self.state.emails_failed),
            last_sent_time=self.state.emails_sent[-1].timestamp if self.state.emails_sent else None,
            last_operation_success=len(self.state.error_history) == 0 or 
                                  self.state.error_history[-1][0] < self._steps_taken - 1,
        )
        
        # Calendar status
        next_meeting = None
        if self.state.meetings:
            meetings_sorted = sorted(
                self.state.meetings.values(),
                key=lambda m: m.scheduled_time
            )
            next_meeting = meetings_sorted[0]
        
        available_slots = []
        # Generate available time slots (mock)
        for i in range(3):
            start = now + timedelta(hours=2 + i*2)
            end = start + timedelta(hours=1)
            available_slots.append(TimeWindow(start_time=start, end_time=end))
        
        calendar_status = CalendarStatus(
            meeting_count=len(self.state.meetings),
            next_meeting=next_meeting,
            conflicts=[],
            available_slots=available_slots,
            busy_hours=sum(m.duration_minutes for m in self.state.meetings.values()) // 60,
        )
        
        # Language context
        language_context = LanguageContext(
            detected_language=self.state.detected_language,
            confidence=self.state.language_confidence,
            alternative_languages=[],
            translation_available=len(self.state.translation_history) > 0,
            last_translation=self.state.translation_history[-1][2][:100] if self.state.translation_history else None,
            language_family=self._get_language_family(self.state.detected_language),
            character_set_detected=self._detect_charset("sample text" if not self.state.translation_history else self.state.translation_history[-1][2]),
            fallback_chain=[LanguageEnum.EN] if self.state.detected_language != LanguageEnum.EN else [],
        )
        
        # Gesture context with enhanced fields
        gesture_sequence = None
        contextual_interpretation = None
        if len(self.state.gesture_history) >= 2:
            gesture_sequence = self.state.gesture_history[-2:]
        
        gesture_context = GestureContext(
            last_gesture=self.state.last_gesture,
            recognized_gesture=self.state.last_gesture,
            confidence=0.85 + random.random() * 0.15,
            suggested_action="Process last gesture" if self.state.last_gesture else None,
            gesture_history=self.state.gesture_history[-10:],
            gesture_sequence=gesture_sequence,
            last_intensity=0.5 + random.random() * 0.5,
            gesture_duration_ms=random.randint(100, 1000) if self.state.last_gesture else None,
            contextual_interpretation=contextual_interpretation,
        )
        
        # System state
        system_state = SystemState(
            timestamp=now,
            episode_step=self._steps_taken,
            memory_usage_mb=50.0 + random.random() * 100,
            error_count=len(self.state.error_history),
            last_error=self.state.error_history[-1][1] if self.state.error_history else None,
            system_healthy=len(self.state.error_history) < 5,
        )
        
        # Get task description
        task_desc = None
        if self.state.current_task_id is not None:
            task = self.state.tasks.get(self.state.current_task_id)
            if task:
                task_desc = task.description
        
        return Observation(
            email_status=email_status,
            calendar_status=calendar_status,
            language_context=language_context,
            gesture_context=gesture_context,
            system_state=system_state,
            inbox=self.state.emails_pending[:10],
            recent_meetings=list(self.state.meetings.values())[:5],
            task_description=task_desc,
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, bool, Dict[str, Any]]:
        """
        Execute one step of environment.
        
        Args:
            action: Action to execute
        
        Returns:
            observation: Current observation
            reward: Reward signal
            terminated: Episode termination flag
            truncated: Episode truncation flag (max steps)
            info: Additional info
        """
        self._steps_taken += 1
        self.state.episode_step = self._steps_taken
        self.state.last_action_time = datetime.utcnow()
        
        # Validate action
        is_valid, error_msg = self._validate_action(action)
        if not is_valid:
            result = ActionResult(
                action_type=action.type if hasattr(action, 'type') else "unknown",
                success=False,
                message=f"Invalid action: {error_msg}",
                error_code="INVALID_ACTION",
            )
            self.state.record_error(error_msg)
        else:
            # Route action to appropriate handler
            if isinstance(action, EmailAction):
                result = self._process_email_action(action)
            elif isinstance(action, MeetingAction):
                result = self._process_meeting_action(action)
            elif isinstance(action, TranslationAction):
                result = self._process_translation_action(action)
            elif isinstance(action, GestureAction):
                result = self._process_gesture_action(action)
            elif isinstance(action, NoOpAction):
                result = self._process_noop_action(action)
            elif isinstance(action, WhatsAppAction):
                result = self._process_whatsapp_action(action)
            elif isinstance(action, SearchAction):
                result = self._process_search_action(action)
            elif isinstance(action, SummarizeAction):
                result = self._process_summarize_action(action)
            elif isinstance(action, CodeGenAction):
                result = self._process_code_gen_action(action)
            elif isinstance(action, CommandExecAction):
                result = self._process_cmd_exec_action(action)
            elif isinstance(action, DebugAction):
                result = self._process_debug_action(action)
            else:
                result = ActionResult(
                    action_type="unknown",
                    success=False,
                    message="Unknown action type",
                    error_code="UNKNOWN_ACTION",
                )
                self.state.record_error("Unknown action type")
        
        # Compute reward
        reward_value, reward_breakdown = self._compute_reward(result)
        self._episode_return += reward_value
        
        # Check episode termination conditions
        terminated = False
        truncated = False
        
        # Terminate if task completed
        if (self.state.current_task_id is not None and 
            self.state.tasks.get(self.state.current_task_id, Task(0, "", "")).completed):
            terminated = True
        
        # Truncate if max steps reached
        if self._steps_taken >= self.config.max_episode_steps:
            truncated = True
        
        # Build info dict
        info = {
            "action_result": result.model_dump(),
            "steps_taken": self._steps_taken,
            "max_steps": self.config.max_episode_steps,
            "truncated": truncated,
            "terminated": terminated,
            "episode_return": self._episode_return,
        }
        
        # Get observation
        observation = self._get_observation()
        
        # Build reward
        reward = Reward(
            total_reward=reward_value,
            breakdown=reward_breakdown,
            episode_return=self._episode_return,
            is_episode_complete=terminated,
            completion_reason="Task completed" if terminated else None,
        )
        
        return observation, reward, terminated, truncated, info

    def set_task(self, task: Task) -> None:
        """Set task for current episode"""
        self.state.current_task_id = task.task_id
        self.state.tasks[task.task_id] = task

    def close(self) -> None:
        """Clean up environment resources"""
        self.state.reset()
        self._episode_return = 0.0
        self._steps_taken = 0
