from enum import Enum
from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ============================================================================
# ENUMS
# ============================================================================

class LanguageEnum(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    ZH = "zh"
    JA = "ja"


class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MeetingTypeEnum(str, Enum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"


class GestureEnum(str, Enum):
    # Basic gestures
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    DOUBLE_TAP = "double_tap"
    LONG_PRESS = "long_press"
    PINCH_ZOOM = "pinch_zoom"
    VOICE_COMMAND = "voice_command"
    # Advanced gestures
    TWO_FINGER_TAP = "two_finger_tap"
    THREE_FINGER_SWIPE = "three_finger_swipe"
    ROTATION = "rotation"
    HOLD_AND_DRAG = "hold_and_drag"


# ============================================================================
# ACTION MODELS
# ============================================================================

class EmailAction(BaseModel):
    """Send email action"""
    type: str = "email"
    recipient_id: int = Field(..., ge=0, le=10000)
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=5000)
    priority: PriorityEnum = PriorityEnum.MEDIUM
    language: LanguageEnum = LanguageEnum.EN
    cc_ids: List[int] = Field(default_factory=list)
    bcc_ids: List[int] = Field(default_factory=list)
    location: str = Field(default="Office", max_length=100)
    send_real: bool = Field(default=False, description="Send real email if configured")

    @validator("cc_ids", "bcc_ids")
    def validate_cc_bcc(cls, v):
        if len(v) > 50:
            raise ValueError("Cannot CC/BCC more than 50 recipients")
        return v


class MeetingAction(BaseModel):
    """Schedule meeting action"""
    type: str = "meeting"
    title: str = Field(..., min_length=1, max_length=100)
    attendee_ids: List[int] = Field(..., min_length=1, max_length=100)
    scheduled_time: datetime
    duration_minutes: int = Field(..., ge=15, le=480)
    meeting_type: MeetingTypeEnum = MeetingTypeEnum.VIRTUAL
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    @validator("attendee_ids")
    def validate_attendees(cls, v):
        if len(set(v)) != len(v):
            raise ValueError("Duplicate attendee IDs")
        return v


class TranslationAction(BaseModel):
    """Translate text action"""
    type: str = "translate"
    text: str = Field(..., min_length=1, max_length=5000)
    source_language: LanguageEnum
    target_language: LanguageEnum

    @validator("text")
    def validate_languages_differ(cls, v, values):
        if "source_language" in values and "target_language" in values:
            if values["source_language"] == values["target_language"]:
                raise ValueError("Source and target languages must differ")
        return v


class GestureAction(BaseModel):
    """Interpret gesture action"""
    type: str = "gesture"
    gesture_code: GestureEnum
    intensity: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Union[str, float, int]] = Field(default_factory=dict)


class NoOpAction(BaseModel):
    """No-operation action"""
    type: str = "noop"
    reason: Optional[str] = None


# ============================================================================
# NEW COMPREHENSIVE ACTION TYPES
# ============================================================================

class WhatsAppAction(BaseModel):
    """Send WhatsApp message action"""
    type: str = "whatsapp"
    phone_number: str = Field(..., min_length=10, max_length=20, description="E.164 format: +1234567890")
    message: str = Field(..., min_length=1, max_length=5000)
    media_url: Optional[str] = Field(None, description="Optional media URL")
    media_type: Optional[str] = Field(None, description="image, document, video, audio")
    use_template: bool = Field(default=False, description="Use template message")
    template_name: Optional[str] = Field(None, description="Template name if use_template=True")
    template_params: List[str] = Field(default_factory=list)


class SearchAction(BaseModel):
    """Web search action"""
    type: str = "search"
    query: str = Field(..., min_length=1, max_length=500)
    search_type: str = Field(default="web", description="web, image, news")
    num_results: int = Field(default=10, ge=1, le=50)
    provider: Optional[str] = Field(None, description="google, bing, duckduckgo")
    language: Optional[str] = Field(None)


class SummarizeAction(BaseModel):
    """Content summarization action"""
    type: str = "summarize"
    content: str = Field(..., min_length=1, max_length=10000, description="Text or URL to summarize")
    style: str = Field(default="detailed", description="brief, detailed, bullet_points, executive, key_insights")
    max_length: Optional[int] = Field(None, description="Max summary length in words")


class CodeGenAction(BaseModel):
    """Code generation action"""
    type: str = "code_gen"
    description: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="python", description="python, javascript, java, go, rust, sql, etc.")
    task: str = Field(default="generate", description="generate, fix, refactor, explain, test, document")
    code: Optional[str] = Field(None, description="Code to fix/refactor/explain")
    context: Optional[str] = Field(None, description="Additional context")


class CommandExecAction(BaseModel):
    """Execute system command action"""
    type: str = "cmd_exec"
    command: str = Field(..., min_length=1, max_length=2000)
    shell: str = Field(default="powershell", description="powershell or cmd")
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    require_confirmation: bool = Field(default=True)
    working_dir: Optional[str] = Field(None)


class DebugAction(BaseModel):
    """Code debugging and error correction action"""
    type: str = "debug"
    error_text: str = Field(..., min_length=1, max_length=5000, description="Stack trace or error message")
    language: str = Field(default="python", description="python, javascript, java, etc.")
    code: Optional[str] = Field(None, description="Code snippet with error")
    action: str = Field(default="analyze", description="analyze, correct, explain")


# Union type for all actions
Action = Union[
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
    DebugAction
]


# ============================================================================
# OBSERVATION MODELS
# ============================================================================

class Email(BaseModel):
    """Email record"""
    email_id: int
    sender_id: int
    subject: str
    body: str
    language: LanguageEnum
    timestamp: datetime
    read: bool = False


class Meeting(BaseModel):
    """Meeting record"""
    meeting_id: int
    title: str
    attendee_ids: List[int]
    scheduled_time: datetime
    duration_minutes: int
    meeting_type: MeetingTypeEnum
    location: Optional[str] = None
    created_at: datetime


class TimeWindow(BaseModel):
    """Available time slot"""
    start_time: datetime
    end_time: datetime
    available: bool = True


class EmailStatus(BaseModel):
    """Email system status"""
    pending_count: int = Field(..., ge=0)
    inbox_count: int = Field(..., ge=0)
    sent_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    last_sent_time: Optional[datetime] = None
    last_operation_success: bool = True


class CalendarStatus(BaseModel):
    """Calendar system status"""
    meeting_count: int = Field(..., ge=0)
    next_meeting: Optional[Meeting] = None
    conflicts: List[Meeting] = Field(default_factory=list)
    available_slots: List[TimeWindow] = Field(default_factory=list)
    busy_hours: int = Field(..., ge=0)


class LanguageContext(BaseModel):
    """Language detection and processing context with fallback chain"""
    detected_language: LanguageEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    alternative_languages: List[LanguageEnum] = Field(default_factory=list)
    translation_available: bool = True
    last_translation: Optional[str] = None
    language_family: Optional[str] = None  # Indo-European, Sino-Tibetan, etc.
    character_set_detected: Optional[str] = None  # Latin, CJK, Cyrillic, etc.
    fallback_chain: List[LanguageEnum] = Field(default_factory=list)  # Fallback languages


class GestureContext(BaseModel):
    """Gesture recognition context with sequence and intensity awareness"""
    last_gesture: Optional[GestureEnum] = None
    recognized_gesture: Optional[GestureEnum] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    suggested_action: Optional[str] = None
    gesture_history: List[GestureEnum] = Field(default_factory=list)
    gesture_sequence: Optional[List[GestureEnum]] = None  # Multi-gesture sequence
    last_intensity: float = Field(default=0.5, ge=0.0, le=1.0)  # Gesture intensity
    gesture_duration_ms: Optional[float] = None  # Duration of gesture
    contextual_interpretation: Optional[str] = None  # Context-aware meaning


class SystemState(BaseModel):
    """System operational state"""
    timestamp: datetime
    episode_step: int = Field(..., ge=0)
    memory_usage_mb: float = Field(..., ge=0.0)
    error_count: int = Field(..., ge=0)
    last_error: Optional[str] = None
    system_healthy: bool = True


class Observation(BaseModel):
    """Complete observation returned by environment"""
    email_status: EmailStatus
    calendar_status: CalendarStatus
    language_context: LanguageContext
    gesture_context: GestureContext
    system_state: SystemState
    inbox: List[Email] = Field(default_factory=list)
    recent_meetings: List[Meeting] = Field(default_factory=list)
    task_description: Optional[str] = None


# ============================================================================
# REWARD MODELS
# ============================================================================

class RewardBreakdown(BaseModel):
    """Detailed reward components with granular shaping"""
    # Core action outcomes
    action_success: float = Field(..., ge=-1.0, le=1.0, description="Action correctness")
    task_progress: float = Field(..., ge=-1.0, le=1.0, description="Task completion progress")
    
    # Efficiency and quality bonuses
    efficiency_penalty: float = Field(default=0.0, ge=-1.0, le=0.0, description="Penalty for repeated actions")
    parameter_quality: float = Field(default=0.0, ge=-1.0, le=1.0, description="Quality of action parameters")
    temporal_efficiency: float = Field(default=0.0, ge=-1.0, le=1.0, description="Speed bonus for task completion")
    
    # Error and context handling
    error_penalty: float = Field(default=0.0, ge=-1.0, le=0.0, description="Penalty for errors")
    context_awareness: float = Field(default=0.0, ge=-1.0, le=1.0, description="Action relevance to task")
    
    # Language and communication
    language_accuracy: float = Field(default=0.0, ge=-1.0, le=1.0, description="Multilingual handling quality")
    
    # Additional metrics
    consistency_bonus: float = Field(default=0.0, ge=-1.0, le=1.0, description="Bonus for coherent sequences")
    state_stability: float = Field(default=0.0, ge=-1.0, le=1.0, description="Penalty for state conflicts")


class Reward(BaseModel):
    """Reward signal sent to agent"""
    total_reward: float = Field(..., ge=-1.0, le=1.0)
    breakdown: RewardBreakdown
    episode_return: float = Field(default=0.0)
    is_episode_complete: bool = False
    completion_reason: Optional[str] = None


# ============================================================================
# INFO/METADATA MODELS
# ============================================================================

class ActionResult(BaseModel):
    """Result of executing an action"""
    action_type: str
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_code: Optional[str] = None
    details: Dict[str, Union[str, int, float, bool, List, None]] = Field(default_factory=dict)


class StepInfo(BaseModel):
    """Additional info from step() call"""
    action_result: ActionResult
    task_status: Optional[str] = None
    steps_taken: int = 0
    max_steps: int = 100
    truncated: bool = False
    terminated: bool = False


class EnvironmentConfig(BaseModel):
    """Environment configuration"""
    max_episode_steps: int = Field(default=100, ge=1)
    step_delay_ms: int = Field(default=100, ge=0)
    seed: Optional[int] = None
    enable_logging: bool = True
    language_default: LanguageEnum = LanguageEnum.EN
    num_contacts: int = Field(default=1000, ge=10)
    num_meetings_capacity: int = Field(default=500, ge=10)
