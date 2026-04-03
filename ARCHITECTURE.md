"""
ARCHITECTURE DOCUMENTATION
APEXEnv (Autonomous Productivity EXecutor)

This document explains the internal architecture and how step() works.
"""

# ============================================================================
# OPENENV INTERFACE
# ============================================================================
"""
APEXEnv follows the OpenEnv specification:

reset() : Observation
    Initialize episode to initial state.
    Returns initial observation.
    Clears all episode-specific data (emails, meetings, tasks).
    Preserves: contacts database, configuration.

step(action: Action) : Tuple[Observation, Reward, bool, bool, dict]
    Execute one action in the environment.
    
    Returns:
    - observation: Current system state as dict
    - reward: Reward signal (float in [-1, 1])
    - terminated: Whether episode reached end goal
    - truncated: Whether episode reached max steps
    - info: Additional metadata and debugging info

state() : APEXEnvState
    Return current internal state (for inspection only).
    Does not modify environment.

close() : None
    Clean up resources.
"""

# ============================================================================
# INTERNAL STATE STRUCTURE
# ============================================================================
"""
APEXEnvState contains 5 subsystems:

1. EMAIL SYSTEM
   - emails_sent: List of successfully sent emails
   - emails_pending: List of queued emails
   - emails_failed: List of failed sends
   Tracks all email operations with full audit trail.

2. CALENDAR SYSTEM
   - meetings: Dict[meeting_id → Meeting]
   - Validates no conflicts (time + attendee overlap)
   - Checks all times are in future
   
3. CONTACT DATABASE
   - contacts: Dict[contact_id → Contact]
   - Initialized once at environment creation
   - Persists across episodes
   - Contains 100-1000 contacts with multilingual support

4. TASK MANAGEMENT
   - tasks: Dict[task_id → Task]
   - current_task_id: Currently active task
   - Tracks required_actions vs completed_actions
   - Progress computed as: completed / required

5. LANGUAGE & GESTURE TRACKING
   - detected_language: Current language (default EN)
   - language_confidence: Detection score [0.0, 1.0]
   - translation_history: List of (src, tgt, text) tuples
   - gesture_history: List of recent gestures
   - last_gesture: Most recent gesture

6. EPISODE METRICS
   - episode_step: Current step counter
   - episode_reward: Accumulated reward
   - action_history: List of (step, action_type, success)
   - error_history: List of (step, error_message)
"""

# ============================================================================
# STEP() EXECUTION FLOW
# ============================================================================
"""
step(action: Action) executes in 7 phases:

PHASE 1: PREPARE
    - Time: 1ms
    - Increment step counter
    - Record timestamp
    - Details: _steps_taken++, last_action_time = now()

PHASE 2: VALIDATE ACTION
    - Time: 50ms
    - Check action type is recognized
    - Validate field constraints:
      * EmailAction: recipient exists, no empty subject/body
      * MeetingAction: attendees exist, time is future
      * TranslationAction: text not empty, languages differ
      * GestureAction: intensity in [0.0, 1.0]
    - Return (is_valid: bool, error_msg: Optional[str])
    
    If invalid:
        → Create ActionResult(success=False, error_code)
        → Record error in error_history
        → Skip to PHASE 6 (reward)

PHASE 3: ROUTE ACTION
    - Time: 10ms
    - Determine action handler based on type:
        EmailAction → _process_email_action()
        MeetingAction → _process_meeting_action()
        TranslationAction → _process_translation_action()
        GestureAction → _process_gesture_action()
        NoOpAction → _process_noop_action()

PHASE 4: EXECUTE HANDLER
    - Time: 100-500ms (varies by type)
    
    Email Handler:
        - Create Email record with timestamp
        - Add to emails_sent list
        - Record action in action_history
        - Return ActionResult(success=True)
    
    Meeting Handler:
        - Create Meeting record
        - Check for conflicts with existing meetings
            * Check time overlap
            * Check attendee overlap
        - If conflict: return ActionResult(success=False, error_code="MEETING_CONFLICT")
        - If valid: add to meetings dict, return success
    
    Translation Handler:
        - Simulate translation quality [0.8, 1.0]
        - Record in translation_history
        - Update detected_language
        - Update language_confidence
        - Return ActionResult(success=True)
    
    Gesture Handler:
        - Append gesture to gesture_history
        - Set last_gesture
        - Map gesture to suggested action
        - Return ActionResult(success=True)

PHASE 5: COMPUTE REWARD & UPDATE STATE
    - Time: 30ms
    - Calculate reward components:
    
    action_success:
        if action succeeded: +1.0
        else: -1.0
    
    task_progress:
        if no task: 0.0
        else: (completed_actions / required_actions)
    
    efficiency_penalty:
        if last 5 actions contain 3+ of same type: -0.2
        else: 0.0
    
    error_penalty:
        if action failed: -0.3
        else: 0.0
    
    language_accuracy:
        if action is translation: +0.2 * confidence
        elif action is email: +0.1 (multilingual email)
        else: 0.0
    
    Breakdown: RewardBreakdown(
        action_success,
        task_progress,
        efficiency_penalty,
        error_penalty,
        language_accuracy,
    )
    
    total_reward = (action_success + task_progress + 
                   efficiency_penalty + error_penalty + 
                   language_accuracy) / 5.0
    total_reward = clamp(total_reward, -1.0, 1.0)
    
    Accumulate: episode_reward += total_reward

PHASE 6: CHECK TERMINATION
    - Time: 10ms
    - Terminated conditions (episode ends):
        1. Task completed: all required_actions marked as complete
        2. Manual termination: via complete_task()
    
    - Truncated conditions (episode bounds):
        1. Max steps reached: episode_step >= max_episode_steps
    
    Set terminated, truncated flags

PHASE 7: GENERATE OBSERVATION & RETURN
    - Time: 20ms
    - Convert APEXEnvState → Observation:
    
    Observation components:
        - email_status: From emails_sent/pending/failed counts
        - calendar_status: From meetings list
        - language_context: From detected_language, translation_history
        - gesture_context: From gesture_history, last_gesture
        - system_state: Episode metrics, memory, errors
        - inbox: First 10 emails from emails_pending
        - recent_meetings: First 5 upcoming meetings
        - task_description: If task active, its description
    
    - Create Reward object:
        Reward(
            total_reward=reward_value,
            breakdown=breakdown,
            episode_return=episode_reward,
            is_episode_complete=terminated,
            completion_reason="Task completed" if terminated else None,
        )
    
    - Create info dict:
        {
            "action_result": ActionResult dict,
            "steps_taken": self._steps_taken,
            "max_steps": self.config.max_episode_steps,
            "truncated": truncated,
            "terminated": terminated,
            "episode_return": self._episode_return,
        }
    
    - Return tuple:
        (observation, reward, terminated, truncated, info)

TOTAL TIME PER STEP: ~200-700ms (including simulated delays)
"""

# ============================================================================
# DATA FLOW DIAGRAMS
# ============================================================================
"""
INPUT FLOW:
    Agent
        ↓
    Action (EmailAction | MeetingAction | TranslationAction | GestureAction)
        ↓
    Validate
        ├─ Valid → Handler → ActionResult
        └─ Invalid → Error → ActionResult(success=False)

STATE UPDATE FLOW:
    ActionResult
        ↓
    Handler-specific update:
        - Email: emails_sent.append(email)
        - Meeting: meetings[id] = meeting
        - Translation: translation_history.append(...)
        - Gesture: gesture_history.append(gesture)
        ↓
    Record in action_history
    Record if error in error_history
        ↓
    APEXEnvState updated

REWARD FLOW:
    ActionResult(success) → action_success
    Task progress → task_progress
    Recent actions → efficiency_penalty
    Error flag → error_penalty
    Language quality → language_accuracy
        ↓
    RewardBreakdown(5 components)
        ↓
    Average & normalize to [-1, 1]
        ↓
    Accumulate in episode_return
        ↓
    Reward object

OUTPUT FLOW:
    APEXEnvState → Observation
    RewardBreakdown → Reward
    Flags → terminated, truncated
    Metadata → info dict
        ↓
    Return (Observation, Reward, bool, bool, dict)
        ↓
    Agent
"""

# ============================================================================
# EXAMPLE: MULTI-STEP EPISODE
# ============================================================================
"""
Setup:
    env = APEXEnv(EnvironmentConfig(max_episode_steps=3))
    obs = env.reset()  # episode_step=0, episode_reward=0.0
    
    task = Task(
        task_id=1,
        description="Send email and schedule meeting",
        required_actions=["email", "meeting"],
    )
    env.set_task(task)

Step 1: Send Email
    action = EmailAction(
        recipient_id=0,
        subject="Meeting",
        body="Hi Alice, let's sync",
        language=EN,
    )
    
    Execution:
        Phase 1: _steps_taken = 1
        Phase 2: Validate → recipient 0 exists ✓
        Phase 3: Route → _process_email_action()
        Phase 4: Create Email, add to emails_sent
                 Record: (step=1, type="email", success=True)
        Phase 5: action_success = +1.0 ✓
                task_progress = 1/2 = 0.5
                Reward breakdown: [1.0, 0.5, 0, 0, 0.1] → avg = 0.32
        Phase 6: terminated=False, truncated=False (step 1/3)
        Phase 7: obs.email_status.sent_count = 1
                 obs.system_state.episode_step = 1
    
    Return: (obs, Reward(0.32), False, False, info)
    episode_reward = 0.32

Step 2: Schedule Meeting
    action = MeetingAction(
        title="Sync",
        attendee_ids=[0, 1],
        scheduled_time=now + 1 day,
        duration_minutes=30,
    )
    
    Execution:
        Phase 1: _steps_taken = 2
        Phase 2: Validate → attendees exist ✓
        Phase 3: Route → _process_meeting_action()
        Phase 4: Create Meeting, check conflicts → none
                 Add to meetings dict
                 Record: (step=2, type="meeting", success=True)
                 Mark task action "meeting" complete
        Phase 5: action_success = +1.0 ✓
                task_progress = 2/2 = 1.0 (TASK COMPLETE!)
                Reward: [1.0, 1.0, 0, 0, 0] → avg = 0.4
        Phase 6: terminated=True ✓ (task complete)
        Phase 7: obs.calendar_status.meeting_count = 1
    
    Return: (obs, Reward(0.4), True, False, info)
    episode_reward = 0.72

Episode ends because terminated=True

Final metrics:
    episode_return = 0.72
    steps_taken = 2
    task completion = 1.0
"""

# ============================================================================
# VALIDATION RULES
# ============================================================================
"""
EmailAction:
    - recipient_id: 0-10000
    - subject: <1, 200> chars
    - body: <1, 5000> chars
    - priority: enum
    - language: enum
    - cc_ids, bcc_ids: <0, 50> each
    - Recipient must exist in contacts

MeetingAction:
    - title: <1, 100> chars
    - attendee_ids: <1, 100> attendees, no duplicates
    - scheduled_time: must be future
    - duration_minutes: <15, 480>
    - meeting_type: enum
    - location: max 200 chars
    - All attendees must exist
    - No time/attendee conflicts

TranslationAction:
    - text: <1, 5000> chars
    - source_language: enum
    - target_language: enum
    - source ≠ target

GestureAction:
    - gesture_code: enum
    - intensity: [0.0, 1.0]
    - timestamp: optional (defaults to now)
    - metadata: optional
"""

# ============================================================================
# REWARD POLICY
# ============================================================================
"""
Reward Range: [-1.0, +1.0]

Reward Components (each normalized to [-1, 1]):

1. ACTION_SUCCESS (weight: 1/5)
   Correct action: +1.0
   Invalid action: -1.0

2. TASK_PROGRESS (weight: 1/5)
   Range [0.0, 1.0] based on completed_actions / required_actions
   
3. EFFICIENCY_PENALTY (weight: 1/5)
   Encourages action diversity
   Repeated action type 3+ times in last 5 steps: -0.2
   Otherwise: 0.0

4. ERROR_PENALTY (weight: 1/5)
   Action failed: -0.3
   Action succeeded: 0.0

5. LANGUAGE_ACCURACY (weight: 1/5)
   Translation: +0.2 * language_confidence
   Email: +0.1 (for handling multilingual)
   Other: 0.0

Final: average of 5 components, clamped to [-1, 1]

Accumulated: episode_return = Σ(rewards)
"""

# ============================================================================
# ERROR HANDLING
# ============================================================================
"""
All errors are:
1. Caught and recorded
2. Returned as ActionResult(success=False, error_code)
3. Logged in state.error_history

Example error flow:
    User provides invalid recipient_id 9999
        ↓
    Validation fails: contact not found
        ↓
    Return ActionResult(
        success=False,
        error_code="INVALID_RECIPIENT",
        message="Recipient ID 9999 not found"
    )
        ↓
    Record in error_history: (step=1, "Recipient ID 9999 not found")
        ↓
    Reward: action_success = -1.0
    Reward: error_penalty = -0.3
        ↓
    Total penalty: -0.26 reward
        ↓
    Error tracked, episode continues (unless max errors reached)
"""

# ============================================================================
# CONTACTS AND SAMPLING
# ============================================================================
"""
Contacts are initialized once:
    - 100 synthetic contacts created
    - contact_id: 0-99 (or up to num_contacts)
    - Names: Alice J., Bob S., Charlie H., ...
    - Email: contact{id}@example.com
    - Languages: Most have [EN], some have [EN, ES]
    - Timezone: "UTC" (default)

Getting a contact:
    contact = env.state.get_contact(0)
    name = contact.name  # "Alice J."
    email = contact.email  # "contact0@example.com"

Contacts persist across episodes:
    env.reset()  # Does NOT clear contacts
    env.close()  # Does NOT clear contacts
"""

# ============================================================================
# EXTENSIBILITY
# ============================================================================
"""
To add new action type:

1. Create Pydantic model in models/schemas.py
   class MyAction(BaseModel):
       type: str = "myaction"
       field1: str
       field2: int

2. Add to Union in schemas.py
   Action = Union[..., MyAction]

3. Add handler in environment.py
   def _process_myaction_action(self, action: MyAction) → ActionResult:
       # Implementation
       return ActionResult(...)

4. Add route in step()
   elif isinstance(action, MyAction):
       result = self._process_myaction_action(action)

5. Add validation in _validate_action()
   elif isinstance(action, MyAction):
       if not valid:
           return False, error_msg
       return True, None
"""

print(__doc__)
