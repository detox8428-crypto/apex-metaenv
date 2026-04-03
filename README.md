# APEX Environment 🚀

**APEX Environment** is a sophisticated simulation and training system designed for developing, testing, and evaluating intelligent agents. It provides a rich, multi-action environment with complete state management, task definition, and performance evaluation capabilities.

## What is APEX?

APEX (Advanced Platform for Experiential Learning) is a training environment that simulates realistic workplace scenarios. Agents interact with the environment through various action types, receive rewards for successful actions, and can be evaluated on task completion.

### Core Capabilities

✓ **Multi-Action Support** - Email, meetings, translation, gestures
✓ **State Management** - Complete environment state tracking
✓ **Task System** - Define and evaluate specific tasks
✓ **Reward System** - Real-time feedback on agent performance
✓ **REST API** - Remote access and integration
✓ **Python Client** - Easy integration with Python scripts
✓ **Interactive Documentation** - Swagger UI for API exploration
✓ **Production Ready** - Docker support, logging, error handling

## Quick Start (2 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run_server.py
```

Expected output:
```
APEX ENVIRONMENT - FastAPI Server
Starting server...
Host: 0.0.0.0
Port: 8000

📖 Interactive docs: http://localhost:8000/docs
📖 Alternative docs: http://localhost:8000/redoc

Press CTRL+C to stop
```

### 3. Test with Examples
```bash
python client_example.py
```

## Setup Instructions

### Docker Deployment

#### Option 1: Simple Docker Build
```bash
docker build -t apex-env .
docker run -p 8000:8000 apex-env
```

#### Option 2: Docker Compose
```bash
docker-compose up
```

## Supported Tasks

### Email Task
Send emails to recipients with appropriate subject and body content:
- recipient_id: Contact ID
- subject: Email subject
- body: Email body
- language: EN, ES, FR, DE, ZH, JA
- priority: LOW, MEDIUM, HIGH

### Meeting Task
Schedule meetings with specific attendees and timing:
- title: Meeting title
- attendee_ids: List of attendee IDs
- scheduled_time: RFC 3339 datetime
- duration_minutes: Meeting duration
- meeting_type: VIRTUAL, IN_PERSON, HYBRID

### Translation Task
Translate text between different languages:
- text: Text to translate
- source_language: Source language code
- target_language: Target language code

### Gesture Task
Execute gesture-based commands:
- gesture_code: SWIPE_LEFT, SWIPE_RIGHT, DOUBLE_TAP, etc.
- intensity: 0.0 to 1.0

### No-Op Task
Execute a no-operation action:
- reason: Optional reason for waiting

## REST API

### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Server health check |
| POST | `/reset` | Reset environment |
| POST | `/step` | Execute action |
| GET | `/state` | Get current state |
| POST | `/task` | Set task |
| POST | `/evaluate` | Grade performance |

**API Documentation**: http://localhost:8000/docs (Swagger UI)

## Python Client Usage

```python
from client_example import APEXClient

client = APEXClient("http://localhost:8000")

# Reset environment
client.reset(seed=42)

# Set task
client.set_task("email", {
    "recipient_id": 0,
    "subject": "Meeting",
    "body": "schedule"
})

# Execute action
response = client.step({
    "action_type": "email",
    "recipient_id": 0,
    "subject": "Meeting Request",
    "body": "Can we schedule a meeting?"
})

print(f"Reward: {response['reward']}")

# Evaluate
evaluation = client.evaluate("email", {
    "expected_recipient_id": 0,
    "expected_subject": "Meeting",
    "expected_body": "schedule"
})

print(f"Score: {evaluation['score']:.2f}")

client.close()
```

## Configuration

APEX is configured via `openenv.yaml`. Use environment variables to override defaults:

```bash
export API_BASE_URL="http://localhost:8000"
export MODEL_NAME="gpt-3.5-turbo"
export HF_TOKEN="your_token"
```

### Configuration File

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

inference:
  api_base_url: "http://localhost:8000"
  model_name: "gpt-3.5-turbo"
  hf_token: ""

logging:
  level: "INFO"
  file: "apex.log"

environment:
  seed: 42
  max_steps_per_episode: 100
```

## Inference Module

The inference module provides AI-powered action classification and parameter extraction:

```python
from inference import APEXInferenceClient

client = APEXInferenceClient()

# Generate response
response = client.generate_response(
    prompt="What should I do?",
    task_id="task_001"
)

# Classify action
classification = client.classify_action(
    action_description="Send email to John"
)

# Extract parameters
params = client.extract_parameters(
    action_description="Schedule meeting at 2 PM",
    action_type="meeting"
)
```

### Environment Variables

```bash
export API_BASE_URL="http://localhost:8000"
export MODEL_NAME="gpt-3.5-turbo"
export HF_TOKEN="your_token"
export OPENAI_API_KEY="your_key"
```

## Troubleshooting

### Port Already in Use
```bash
python -c "import uvicorn; uvicorn.run('server:app', port=8001)"
```

### ImportError: No module named 'apex_env'
```bash
cd d:\APEX
python run_server.py
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## Production Deployment

1. Install dependencies: `pip install -r requirements.txt`
2. Start server: `python run_server.py`
3. Access API docs: http://localhost:8000/docs

---

✅ **Status**: Production Ready
**Version**: 1.0.0
