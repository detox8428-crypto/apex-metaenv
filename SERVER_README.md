# APEX Environment - FastAPI Server

Clean, production-ready REST API for APEX Environment.

## Quick Start (2 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server
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

### 3. Run Examples (in another terminal)
```bash
python client_example.py
```

This runs 7 complete examples demonstrating all features.

## Interactive API Documentation

Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Try endpoints interactively with the "Try it out" button.

## Six REST Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/reset` | Reset environment |
| POST | `/step` | Execute action |
| GET | `/state` | Get current state |
| POST | `/task` | Set task |
| POST | `/evaluate` | Grade performance |

## Python Client Usage

```python
from client_example import APEXClient

client = APEXClient("http://localhost:8000")

# Reset
client.reset(seed=42)

# Execute email action
response = client.step({
    "action_type": "email",
    "recipient_id": 0,
    "subject": "Test",
    "body": "test content"
})

# Get state
state = client.get_state()

# Evaluate
eval_result = client.evaluate("email", {
    "expected_recipient_id": 0,
    "expected_subject": "Test",
    "expected_body": "content"
})

print(f"Score: {eval_result['score']:.2f}")
client.close()
```

## CURL Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Reset
```bash
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"seed": 42}'
```

### Send Email
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "email",
      "recipient_id": 0,
      "subject": "Test",
      "body": "test"
    }
  }'
```

### Get State
```bash
curl http://localhost:8000/state | jq
```

## Action Types

### Email Action
```json
{
  "action_type": "email",
  "recipient_id": 0,
  "subject": "Subject",
  "body": "Email body",
  "language": "EN",
  "priority": "MEDIUM"
}
```

### Meeting Action
```json
{
  "action_type": "meeting",
  "title": "Meeting",
  "attendee_ids": [0, 1, 2],
  "scheduled_time": "2026-04-05T14:00:00Z",
  "duration_minutes": 60,
  "meeting_type": "VIRTUAL"
}
```

### Translation Action
```json
{
  "action_type": "translation",
  "text": "Text to translate",
  "source_language": "EN",
  "target_language": "ES"
}
```

### Gesture Action
```json
{
  "action_type": "gesture",
  "gesture_code": "SWIPE_LEFT",
  "intensity": 1.0
}
```

### No-Op Action
```json
{
  "action_type": "noop",
  "reason": "Waiting"
}
```

## Docker Deployment

### Option 1: Simple Docker
```bash
docker build -t apex-env .
docker run -p 8000:8000 apex-env
```

### Option 2: Docker Compose
```bash
docker-compose up
```

Then access the API at `http://localhost:8000`

## Files Included

```
server.py                 # FastAPI application
run_server.py            # Startup script
client_example.py        # Python client + 7 examples
SERVER_SETUP_GUIDE.md   # Complete documentation
FASTAPI_SUMMARY.md      # Phase 5 overview
Dockerfile              # Container image
docker-compose.yml      # Multi-container setup
requirements.txt        # Updated with FastAPI dependencies
```

## Complete Workflow Example

```python
from client_example import APEXClient

client = APEXClient()

# 1. Reset environment
client.reset(seed=42)
print("✓ Environment reset")

# 2. Set email task
client.set_task("email", {
    "recipient_id": 0,
    "subject": "Meeting Request",
    "body": "schedule"
})
print("✓ Task set")

# 3. Execute action
response = client.step({
    "action_type": "email",
    "recipient_id": 0,
    "subject": "Meeting Request for Tomorrow",
    "body": "I'd like to schedule a meeting tomorrow."
})
print(f"✓ Step executed, reward: {response['reward']}")

# 4. Get state
state = client.get_state()
print(f"✓ Emails sent: {state['state']['email_system']['sent_count']}")

# 5. Evaluate
evaluation = client.evaluate("email", {
    "expected_recipient_id": 0,
    "expected_subject": "Meeting Request",
    "expected_body": "schedule"
})
print(f"✓ Score: {evaluation['score']:.2f}")
print(f"✓ Success: {evaluation['success']}")

client.close()
```

## Key Features

✓ **REST API** - 6 clean endpoints
✓ **JSON Serialization** - Complete state serialization
✓ **Error Handling** - Comprehensive validation
✓ **Interactive Docs** - Swagger UI at `/docs`
✓ **Docker Support** - Ready to deploy
✓ **Python Client** - Easy integration
✓ **Production Ready** - Logging, error handling, async
✓ **Examples** - 7 complete working scenarios

## Troubleshooting

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill it or use different port
python -c "import uvicorn; uvicorn.run('server:app', port=8001)"
```

**Can't import apex_env:**
```bash
# Ensure apex_env is in Python path
export PYTHONPATH=/path/to/apex:$PYTHONPATH
```

**Connection refused:**
Make sure server is running:
```bash
python run_server.py
```

## Documentation

For complete documentation:
- **Server Setup**: See `SERVER_SETUP_GUIDE.md`
- **Phase 5 Overview**: See `FASTAPI_SUMMARY.md`
- **Interactive Docs**: http://localhost:8000/docs

## Examples

Run all 7 complete examples:
```bash
python client_example.py
```

Examples include:
1. Health check
2. Reset and state retrieval
3. Simple email task
4. Meeting task
5. Multilingual workflow
6. Multiple steps with state tracking
7. Error handling

## Next Steps

1. ✓ Start the server
2. ✓ Try the examples
3. ✓ View interactive docs
4. ✓ Build your own client
5. ✓ Deploy to cloud

## Support

For detailed information:
- **Quick reference**: `TASKS_GRADERS_QUICK_REFERENCE.py`
- **Architecture**: `ARCHITECTURE.md`
- **API docs**: http://localhost:8000/docs
- **Full guide**: `SERVER_SETUP_GUIDE.md`

Enjoy! 🚀
