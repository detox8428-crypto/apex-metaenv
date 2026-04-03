"""
APEX Environment - Web Frontend
Interactive UI for testing and managing APEX environment
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="APEX Environment",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        max-width: 1400px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        padding: 10px 20px;
    }
    .reward-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Session state initialization
if 'episode_history' not in st.session_state:
    st.session_state.episode_history = []
if 'current_reward' not in st.session_state:
    st.session_state.current_reward = 0.0
if 'step_count' not in st.session_state:
    st.session_state.step_count = 0
if 'state_data' not in st.session_state:
    st.session_state.state_data = None

# Helper functions
def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def reset_environment():
    """Reset the environment"""
    try:
        response = requests.post(f"{API_BASE_URL}/reset", timeout=10)
        if response.status_code == 200:
            st.session_state.step_count = 0
            st.session_state.current_reward = 0.0
            st.session_state.episode_history = []
            return True, "Environment reset successfully"
        else:
            return False, f"Reset failed: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_state():
    """Get current environment state"""
    try:
        response = requests.get(f"{API_BASE_URL}/state", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def execute_action(action_data: Dict[str, Any]):
    """Execute an action in the environment"""
    try:
        response = requests.post(f"{API_BASE_URL}/step", json=action_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            st.session_state.step_count += 1
            
            # Extract reward
            if isinstance(result.get('reward'), dict):
                reward = result['reward'].get('total_reward', 0.0)
            else:
                reward = float(result.get('reward', 0.0))
            
            st.session_state.current_reward += reward
            
            # Add to history
            st.session_state.episode_history.append({
                'step': st.session_state.step_count,
                'action': action_data.get('action_type', 'unknown'),
                'reward': reward,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            
            return True, reward, result
        else:
            return False, 0.0, response.json()
    except Exception as e:
        return False, 0.0, {"error": str(e)}

# Main UI
st.title("🤖 APEX Environment Dashboard")
st.markdown("**Autonomous Productivity Executor** - Interactive Training & Testing")

# Header with API status
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    api_health = check_api_health()
    status_color = "🟢" if api_health else "🔴"
    st.metric("API Status", status_color, help="Server health check")

with col2:
    st.metric("Steps Taken", st.session_state.step_count)

with col3:
    st.metric("Episode Reward", f"{st.session_state.current_reward:.4f}")

st.divider()

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📧 Email", "📅 Meeting", "🌍 Translation", "👆 Gesture", "📊 Dashboard"])

# TAB 1: EMAIL
with tab1:
    st.subheader("Send Email Action")
    
    col1, col2 = st.columns(2)
    with col1:
        recipient_id = st.number_input("Recipient ID", min_value=1, max_value=999, value=1, key="email_recipient")
        subject = st.text_input("Subject", placeholder="E.g., Meeting Tomorrow", key="email_subject")
    
    with col2:
        language = st.selectbox(
            "Language",
            ["en", "es", "fr", "de", "zh", "ja", "ru"],
            key="email_language"
        )
        location = st.text_input("Location", value="Office", key="email_location")
    
    body = st.text_area("Body", placeholder="E.g., Let's discuss the project...", height=100, key="email_body")
    
    if st.button("✉️ Send Email", key="btn_email", type="primary"):
        action_data = {
            "action_type": "email",
            "recipient_id": recipient_id,
            "subject": subject,
            "body": body,
            "language": language,
            "location": location
        }
        
        success, reward, result = execute_action(action_data)
        
        if success:
            st.markdown(f"""
            <div class="reward-box">
                <strong>✅ Email Sent!</strong><br>
                Reward: <strong>{reward:.4f}</strong><br>
                Episode Total: {st.session_state.current_reward:.4f}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Error:</strong> {result.get('error', 'Unknown error')}
            </div>
            """, unsafe_allow_html=True)

# TAB 2: MEETING
with tab2:
    st.subheader("Schedule Meeting Action")
    
    col1, col2 = st.columns(2)
    with col1:
        attendees_input = st.text_input(
            "Attendee IDs (comma-separated)",
            value="1,2,3",
            placeholder="E.g., 1,2,3",
            key="meeting_attendees"
        )
        try:
            attendee_ids = [int(x.strip()) for x in attendees_input.split(",")]
        except:
            attendee_ids = [1, 2, 3]
        
        meeting_title = st.text_input("Meeting Title", value="Team Sync", key="meeting_title")
    
    with col2:
        meeting_type = st.selectbox(
            "Meeting Type",
            ["VIRTUAL", "IN_PERSON", "HYBRID"],
            key="meeting_type"
        )
        duration = st.number_input("Duration (minutes)", min_value=15, max_value=480, value=60, step=15, key="meeting_duration")
    
    scheduled_date = st.date_input("Date", key="meeting_date")
    hour = st.slider("Hour (0-23)", min_value=0, max_value=23, value=14, key="meeting_hour")
    
    location = st.text_input("Location", value="Conference Room A", key="meeting_location")
    
    if st.button("📅 Schedule Meeting", key="btn_meeting", type="primary"):
        from datetime import datetime
        scheduled_time = datetime.combine(scheduled_date, datetime.min.time()).replace(hour=hour).isoformat()
        
        action_data = {
            "action_type": "meeting",
            "attendee_ids": attendee_ids,
            "scheduled_time": scheduled_time,
            "duration_minutes": duration,
            "meeting_type": meeting_type,
            "title": meeting_title,
            "location": location
        }
        
        success, reward, result = execute_action(action_data)
        
        if success:
            st.markdown(f"""
            <div class="reward-box">
                <strong>✅ Meeting Scheduled!</strong><br>
                Reward: <strong>{reward:.4f}</strong><br>
                Episode Total: {st.session_state.current_reward:.4f}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Error:</strong> {result.get('error', 'Unknown error')}
            </div>
            """, unsafe_allow_html=True)

# TAB 3: TRANSLATION
with tab3:
    st.subheader("Translate Content")
    
    col1, col2 = st.columns(2)
    with col1:
        source_lang = st.selectbox(
            "Source Language",
            ["en", "es", "fr", "de", "zh", "ja", "ru"],
            key="trans_source"
        )
    
    with col2:
        target_lang = st.selectbox(
            "Target Language",
            ["en", "es", "fr", "de", "zh", "ja", "ru"],
            index=1,
            key="trans_target"
        )
    
    text_to_translate = st.text_area(
        "Text to Translate",
        placeholder="E.g., Hello everyone, let's discuss the meeting tomorrow.",
        height=100,
        key="trans_text"
    )
    
    if st.button("🌍 Translate", key="btn_translate", type="primary"):
        action_data = {
            "action_type": "translation",
            "source_language": source_lang,
            "target_language": target_lang,
            "text": text_to_translate
        }
        
        success, reward, result = execute_action(action_data)
        
        if success:
            st.markdown(f"""
            <div class="reward-box">
                <strong>✅ Translation Complete!</strong><br>
                Reward: <strong>{reward:.4f}</strong><br>
                Episode Total: {st.session_state.current_reward:.4f}
            </div>
            """, unsafe_allow_html=True)
            
            if 'details' in result and 'translated_text' in result['details']:
                st.info(f"**Translated:** {result['details']['translated_text']}")
        else:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Error:</strong> {result.get('error', 'Unknown error')}
            </div>
            """, unsafe_allow_html=True)

# TAB 4: GESTURE
with tab4:
    st.subheader("Perform Gesture")
    
    col1, col2 = st.columns(2)
    with col1:
        gesture_type = st.selectbox(
            "Gesture Type",
            [
                "SWIPE_LEFT", "SWIPE_RIGHT", "SWIPE_UP", "SWIPE_DOWN",
                "TAP", "DOUBLE_TAP", "LONG_PRESS",
                "PINCH", "PINCH_OUT",
                "DRAG", "SCROLL"
            ],
            key="gesture_type"
        )
    
    with col2:
        intensity = st.slider(
            "Intensity (0=light, 1=strong)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            key="gesture_intensity"
        )
    
    st.markdown("**Intensity Guide:**")
    st.caption("0.0-0.3 = Light | 0.3-0.7 = Normal | 0.7-1.0 = Strong")
    
    if st.button("👆 Perform Gesture", key="btn_gesture", type="primary"):
        action_data = {
            "action_type": "gesture",
            "gesture_code": gesture_type,
            "intensity": intensity
        }
        
        success, reward, result = execute_action(action_data)
        
        if success:
            st.markdown(f"""
            <div class="reward-box">
                <strong>✅ Gesture Recognized!</strong><br>
                Reward: <strong>{reward:.4f}</strong><br>
                Episode Total: {st.session_state.current_reward:.4f}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Error:</strong> {result.get('error', 'Unknown error')}
            </div>
            """, unsafe_allow_html=True)

# TAB 5: DASHBOARD
with tab5:
    st.subheader("Environment Dashboard")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Episode Statistics")
        st.metric("Total Steps", st.session_state.step_count)
        st.metric("Episode Reward", f"{st.session_state.current_reward:.4f}")
        if st.session_state.step_count > 0:
            avg_reward = st.session_state.current_reward / st.session_state.step_count
            st.metric("Avg Reward/Step", f"{avg_reward:.4f}")
    
    with col2:
        st.markdown("### Actions")
        if st.button("🔄 Reset Environment", key="btn_reset", type="secondary"):
            success, message = reset_environment()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        
        if st.button("📊 Refresh State", key="btn_refresh"):
            st.session_state.state_data = get_state()
            st.success("State refreshed!")
    
    st.divider()
    
    if st.session_state.episode_history:
        st.markdown("### Episode History")
        
        # Create history dataframe
        import pandas as pd
        df = pd.DataFrame(st.session_state.episode_history)
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "step": st.column_config.NumberColumn("Step", width="small"),
                "action": st.column_config.TextColumn("Action", width="medium"),
                "reward": st.column_config.NumberColumn("Reward", format="%.4f", width="small"),
                "timestamp": st.column_config.TextColumn("Time", width="small"),
            }
        )
        
        # Export history
        if st.button("📥 Export History as JSON", key="btn_export"):
            export_json = json.dumps(st.session_state.episode_history, indent=2)
            st.download_button(
                label="Download",
                data=export_json,
                file_name=f"apex_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    else:
        st.info("No actions taken yet. Start by selecting a tab above and taking an action!")
    
    # Current state
    st.divider()
    st.markdown("### Current State")
    
    if st.button("🔍 Get State", key="btn_get_state"):
        state = get_state()
        if state:
            st.json(state)
        else:
            st.error("Could not fetch state")

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.markdown("### API Configuration")
    st.markdown(f"**Base URL:** {API_BASE_URL}")
    
    health = check_api_health()
    status = "🟢 Connected" if health else "🔴 Disconnected"
    st.markdown(f"**Status:** {status}")
    
    if not health:
        st.warning("⚠️ API not responding. Make sure to run: `python run_server.py`")
    
    st.divider()
    
    st.markdown("### Environment Info")
    st.markdown("""
    **APEX** is an OpenEnv-compliant environment for training productivity agents.
    
    **Supported Actions:**
    - 📧 Email Management
    - 📅 Meeting Scheduling  
    - 🌍 Multilingual Translation
    - 👆 Gesture Recognition
    
    **Reward Components:**
    - Action Success (25%)
    - Task Progress (20%)
    - Language Accuracy (10%)
    - Temporal Efficiency (8%)
    - Context Awareness (8%)
    - ... and 5 more
    
    **Supported Languages:**
    EN, ES, FR, DE, ZH, JA, RU
    """)
    
    st.divider()
    
    st.markdown("### Quick Links")
    st.link_button("📖 API Docs", "http://localhost:8000/docs")
    st.link_button("🔍 Swagger UI", "http://localhost:8000/redoc")
    st.link_button("💚 GitHub", "https://github.com")

# Footer
st.divider()
st.markdown("""
---
**APEX Environment v1.0** | Autonomous Productivity Executor  
Built with ❤️ for agent training and evaluation
""")
