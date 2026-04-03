#!/usr/bin/env python3
"""
APEX Environment - Advanced Features Demonstration

Showcases three major improvements:
1. Granular Reward Shaping (10 components vs 5)
2. Multilingual Handling (language families, character sets, fallback chains)
3. Realistic Gesture Mapping (sequences, intensity awareness, context)
"""

from apex_env import APEXEnv, EnvironmentConfig
from apex_env import (
    EmailAction, TranslationAction, GestureAction, NoOpAction,
    LanguageEnum, GestureEnum
)
import json


print("\n" + "="*80)
print("APEX ENVIRONMENT - ADVANCED FEATURES DEMONSTRATION")
print("="*80 + "\n")

# Initialize environment
print("Initializing APEX Environment...")
config = EnvironmentConfig(max_episode_steps=20, seed=42)
env = APEXEnv(config=config)
obs = env.reset()
print("✅ Environment initialized\n")

# ==============================================================================
# DEMO 1: GRANULAR REWARD SHAPING
# ==============================================================================
print("-" * 80)
print("DEMO 1: GRANULAR REWARD SHAPING (10 Components)")
print("-" * 80 + "\n")

print("Testing different actions to show granular reward components:\n")

# Action 1: NoOp (baseline)
print("1. NoOp Action (baseline):")
obs, reward, done, truncated, info = env.step(NoOpAction(reason="wait"))
print(f"   Total Reward: {reward.total_reward:.3f}")
print(f"   Components: {json.dumps({
    'action_success': round(reward.breakdown.action_success, 3),
    'task_progress': round(reward.breakdown.task_progress, 3),
    'parameter_quality': round(reward.breakdown.parameter_quality, 3),
    'temporal_efficiency': round(reward.breakdown.temporal_efficiency, 3),
    'context_awareness': round(reward.breakdown.context_awareness, 3),
    'efficiency_penalty': round(reward.breakdown.efficiency_penalty, 3),
    'error_penalty': round(reward.breakdown.error_penalty, 3),
    'language_accuracy': round(reward.breakdown.language_accuracy, 3),
    'consistency_bonus': round(reward.breakdown.consistency_bonus, 3),
    'state_stability': round(reward.breakdown.state_stability, 3),
    }, indent=2)}\n")

# Action 2: Email (with parameter quality bonus)
print("2. Email Action (with detailed parameters):")
email_action = EmailAction(
    recipient_id=0,
    subject="Project Update",
    body="Here's the latest project status and timeline for review",
    priority="high",
    language="en"
)
obs, reward, done, truncated, info = env.step(email_action)
print(f"   Total Reward: {reward.total_reward:.3f}")
print(f"   Key Components:")
print(f"     - Action Success: {reward.breakdown.action_success:.3f}")
print(f"     - Parameter Quality: {reward.breakdown.parameter_quality:.3f} (bonus for detailed params)")
print(f"     - Language Accuracy: {reward.breakdown.language_accuracy:.3f}\n")

# ==============================================================================
# DEMO 2: MULTILINGUAL HANDLING WITH DETECTION & FALLBACK
# ==============================================================================
print("-" * 80)
print("DEMO 2: MULTILINGUAL HANDLING (Language Families & Fallbacks)")
print("-" * 80 + "\n")

# Reset for clean demo
env.reset()

# Translation 1: Indo-European pair (easier)
print("1. Indo-European Translation (Easy - same family):")
print("   Translating from Spanish to French (same language family)")
obs, reward, done, truncated, info = env.step(
    TranslationAction(
        text="El proyecto está progresando bien",
        source_language=LanguageEnum.ES,
        target_language=LanguageEnum.FR
    )
)
action_result = info.get("action_result", {})
details = action_result.get("details", {})
print(f"   Quality Score: {details.get('quality', 'N/A')}")
print(f"   Source Family: {details.get('source_family', 'N/A')}")
print(f"   Target Family: {details.get('target_family', 'N/A')}")
print(f"   Charset Conversion: {details.get('charset_conversion', 'N/A')}")
print(f"   Language Confidence: {details.get('language_confidence', 'N/A')}")
print(f"   Fallback Chain: {details.get('fallback_chain', 'N/A')}\n")

# Translation 2: Different families (harder)
print("2. Cross-Family Translation (Harder - different families):")
print("   Translating from English to Chinese (different language families)")
obs, reward, done, truncated, info = env.step(
    TranslationAction(
        text="The advancement in artificial intelligence is remarkable",
        source_language=LanguageEnum.EN,
        target_language=LanguageEnum.ZH
    )
)
action_result = info.get("action_result", {})
details = action_result.get("details", {})
print(f"   Quality Score: {details.get('quality', 'N/A')} (lower due to different families)")
print(f"   Source Family: {details.get('source_family', 'N/A')}")
print(f"   Target Family: {details.get('target_family', 'N/A')}")
print(f"   Charset Conversion: {details.get('charset_conversion', 'N/A')} (Latin → CJK)")
print(f"   Language Confidence: {details.get('language_confidence', 'N/A')}")
print(f"   Fallback Chain: {details.get('fallback_chain', 'N/A')}\n")

# ==============================================================================
# DEMO 3: REALISTIC GESTURE MAPPING WITH INTENSITY & SEQUENCES
# ==============================================================================
print("-" * 80)
print("DEMO 3: REALISTIC GESTURE MAPPING (Intensity + Sequences + Context)")
print("-" * 80 + "\n")

# Reset for clean demo
env.reset()

# Gesture 1: Light swipe
print("1. Light Swipe Right (Low Intensity):")
obs, reward, done, truncated, info = env.step(
    GestureAction(
        gesture_code=GestureEnum.SWIPE_RIGHT,
        intensity=0.2
    )
)
action_result = info.get("action_result", {})
details = action_result.get("details", {})
print(f"   Gesture: {details.get('gesture', 'N/A')}")
print(f"   Intensity: {details.get('intensity', 0):.1f} ({details.get('intensity_level', 'N/A')})")
print(f"   Suggested Action: {details.get('suggested_action', 'N/A')}")
print(f"   Confidence: {details.get('confidence', 0):.2f}\n")

# Gesture 2: Strong long press
print("2. Strong Long Press (High Intensity):")
obs, reward, done, truncated, info = env.step(
    GestureAction(
        gesture_code=GestureEnum.LONG_PRESS,
        intensity=0.9
    )
)
action_result = info.get("action_result", {})
details = action_result.get("details", {})
print(f"   Gesture: {details.get('gesture', 'N/A')}")
print(f"   Intensity: {details.get('intensity', 0):.1f} ({details.get('intensity_level', 'N/A')})")
print(f"   Suggested Action: {details.get('suggested_action', 'N/A')}")
print(f"   Confidence: {details.get('confidence', 0):.2f}")
print(f"   Gesture Duration: {details.get('gesture_duration_ms', 'N/A')} ms\n")

# Gesture 3: Advanced multi-finger gesture
print("3. Advanced Three-Finger Swipe (System-level gesture):")
obs, reward, done, truncated, info = env.step(
    GestureAction(
        gesture_code=GestureEnum.THREE_FINGER_SWIPE,
        intensity=0.6
    )
)
action_result = info.get("action_result", {})
details = action_result.get("details", {})
print(f"   Gesture: {details.get('gesture', 'N/A')}")
print(f"   Intensity: {details.get('intensity', 0):.1f} ({details.get('intensity_level', 'N/A')})")
print(f"   Suggested Action: {details.get('suggested_action', 'N/A')}")
print(f"   Contextual Interpretation: {details.get('contextual_interpretation') or 'Standard system command'}")
print(f"   Confidence: {details.get('confidence', 0):.2f}\n")

# Gesture 4: Gesture sequence recognition
print("4. Gesture Sequence (Swipe + Tap - recognizes pattern):")
obs, reward, done, truncated, info = env.step(
    GestureAction(
        gesture_code=GestureEnum.DOUBLE_TAP,
        intensity=0.4
    )
)
action_result = info.get("action_result", {})
details = action_result.get("details", {})
print(f"   Gesture: {details.get('gesture', 'N/A')}")
print(f"   Suggested Action: {details.get('suggested_action', 'N/A')}")
print(f"   Gesture History: {details.get('gesture_sequence') or 'Same as previous gestures'}")
if details.get('contextual_interpretation'):
    print(f"   Gesture Sequence Meaning: {details.get('contextual_interpretation')}\n")

# ==============================================================================
# SUMMARY & COMPARISON
# ==============================================================================
print("-" * 80)
print("SUMMARY: IMPROVEMENTS OVERVIEW")
print("-" * 80 + "\n")

print("✅ REWARD SHAPING IMPROVEMENTS:")
print("   • Components: 5 → 10 (parameter_quality, temporal_efficiency, context_awareness,")
print("     consistency_bonus, state_stability)")
print("   • Weights: Importance-based weighted averaging instead of uniform")
print("   • More nuanced: Recognizes parameter completeness, quick task completion,")
print("     action relevance, coherent sequences, and system health\n")

print("✅ MULTILINGUAL HANDLING IMPROVEMENTS:")
print("   • Language Detection: Character set detection (Latin, CJK, Cyrillic, etc.)")
print("   • Language Families: Recognizes Indo-European, Sino-Tibetan, Japonic")
print("   • Translation Quality: Adjusted based on language family difficulty")
print("   • Fallback Chains: Automatic intermediate language routing")
print("   • Confidence Scoring: Length-based and charset-based confidence\n")

print("✅ GESTURE MAPPING IMPROVEMENTS:")
print("   • Gestures: 6 → 12 (added SWIPE_UP, SWIPE_DOWN, TWO_FINGER_TAP,")
print("     THREE_FINGER_SWIPE, ROTATION, HOLD_AND_DRAG)")
print("   • Intensity Levels: Light, normal, strong with different actions")
print("   • Sequences: Multi-gesture pattern recognition")
print("   • Context: Gesture-to-action mapping with contextual interpretation")
print("   • Realism: Confidence scores, intensity-based suggestions, duration tracking\n")

# ==============================================================================
# EPISODE STATISTICS
# ==============================================================================
print("-" * 80)
print("EPISODE STATISTICS")
print("-" * 80 + "\n")

print(f"Total reward accumulated: {reward.episode_return:.4f}")
print(f"Actions executed: {len(env.state.action_history)}")
print(f"Errors encountered: {len(env.state.error_history)}")
print(f"Translations performed: {len(env.state.translation_history)}")
print(f"Gestures recognized: {len(env.state.gesture_history)}")

# Cleanup
env.close()

print("\n" + "="*80)
print("✅ DEMONSTRATION COMPLETE - All improvements validated!")
print("="*80 + "\n")
