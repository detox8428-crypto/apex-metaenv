# APEX Environment - Quick Reference Card

## 🚀 Get Started in 2 Minutes

```bash
# 1. Install
pip install -r requirements.txt

# 2. Start
python run_server.py

# 3. Visit
http://localhost:8000/docs
```

---

## 📦 The 4 Required Files

| File | Purpose | Status |
|------|---------|--------|
| **Dockerfile** | Container image - Multi-stage build | ✅ Ready |
| **openenv.yaml** | Configuration - All settings in one file | ✅ Ready |
| **inference.py** | AI inference - OpenAI client + logging | ✅ Ready |
| **README.md** | Documentation - APEX, Tasks, Setup | ✅ Ready |

---

## 🔑 Environment Variables (inference.py reads):

```bash
export API_BASE_URL="http://localhost:8000"      # API endpoint
export MODEL_NAME="gpt-3.5-turbo"                # LLM model
export HF_TOKEN="hf_xxxxx"                       # Hugging Face
```

---

## 📝 Inference.py Logging Format:

```
[START] operation_name (task_id=..., timestamp=...)
[STEP] {"timestamp": "...", "data": {...}}
[END] operation_name (timestamp=..., success=...)
```

---

## 🐳 Docker Commands

```bash
# Build
docker build -t apex-env .

# Run
docker run -p 8000:8000 apex-env

# With Compose
docker-compose up
```

---

## 🎯 5 Supported Tasks

1. **Email** - Send emails with subject/body
2. **Meeting** - Schedule meetings with attendees
3. **Translation** - Translate between languages
4. **Gesture** - Execute gesture commands
5. **No-Op** - Waiting/skip action

---

## 📡 REST API (6 Endpoints)

```
GET    /health              Health check
POST   /reset               Reset environment
POST   /step                Execute action
GET    /state               Get current state
POST   /task                Set task
POST   /evaluate            Grade performance
```

**Docs**: http://localhost:8000/docs (Swagger UI)

---

## 🐍 Python Client

```python
from client_example import APEXClient

client = APEXClient()
client.reset(seed=42)

response = client.step({
    "action_type": "email",
    "recipient_id": 0,
    "subject": "Test",
    "body": "content"
})

print(f"Reward: {response['reward']}")
client.close()
```

---

## 🤖 Inference Module

```python
from inference import APEXInferenceClient

client = APEXInferenceClient()

# Generate response
response = client.generate_response(
    prompt="What to do?",
    task_id="task_001"
)

# Classify action
classification = client.classify_action(
    action_description="Send email"
)

# Extract parameters
params = client.extract_parameters(
    action_description="Schedule meeting",
    action_type="meeting"
)
```

---

## ⚙️ Configuration (openenv.yaml)

```yaml
server:
  host: "0.0.0.0"
  port: 8000

inference:
  api_base_url: "${API_BASE_URL:-http://localhost:8000}"
  model_name: "${MODEL_NAME:-gpt-3.5-turbo}"
  hf_token: "${HF_TOKEN:-}"

logging:
  level: "INFO"
  file: "apex.log"

environment:
  seed: 42
  max_steps_per_episode: 100
```

---

## 📂 File Structure

```
d:\APEX\
├── Dockerfile              ✅ Container image
├── openenv.yaml            ✅ Configuration
├── inference.py            ✅ AI inference
├── README.md               ✅ Documentation
├── server.py               FastAPI app
├── client_example.py       Python client
└── requirements.txt        Dependencies
```

---

## 🧪 Validate Files

```bash
# Run validation
python test_generated_files.py

# Test locally
python run_server.py &
python client_example.py

# Test inference
export API_BASE_URL="http://localhost:8000"
export MODEL_NAME="gpt-3.5-turbo"
export HF_TOKEN="your_token"
python inference.py
```

---

## 🔧 Troubleshooting

**Port already in use?**
```bash
python -c "import uvicorn; uvicorn.run('server:app', port=8001)"
```

**Import errors?**
```bash
export PYTHONPATH=/path/to/apex:$PYTHONPATH
```

**Dependencies missing?**
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| README.md | Main documentation |
| GENERATION_REPORT.md | File details |
| FILES_GENERATED.md | Integration guide |
| SERVER_SETUP_GUIDE.md | Deployment |
| FASTAPI_SUMMARY.md | API reference |

---

## ✅ Verification Checklist

- [x] Dockerfile - Multi-stage build syntax correct
- [x] openenv.yaml - Valid YAML configuration
- [x] inference.py - Reads API_BASE_URL, MODEL_NAME, HF_TOKEN
- [x] inference.py - Logs [START], [STEP], [END] format
- [x] README.md - Explains APEX system
- [x] README.md - Documents all 5 tasks
- [x] README.md - Includes setup instructions

---

## 🎓 Quick Examples

### Example 1: Send Email
```python
client.step({
    "action_type": "email",
    "recipient_id": 0,
    "subject": "Meeting Request",
    "body": "Are you available?"
})
```

### Example 2: Schedule Meeting
```python
client.step({
    "action_type": "meeting",
    "title": "Team Sync",
    "attendee_ids": [0, 1, 2],
    "scheduled_time": "2026-04-05T14:00:00Z",
    "duration_minutes": 60,
    "meeting_type": "VIRTUAL"
})
```

### Example 3: Translate Text
```python
client.step({
    "action_type": "translation",
    "text": "Hello world",
    "source_language": "EN",
    "target_language": "ES"
})
```

---

## 📞 Support

1. Check **README.md** for system documentation
2. Review **GENERATION_REPORT.md** for file details
3. Run **test_generated_files.py** to validate
4. Access **http://localhost:8000/docs** for API docs

---

## 📊 Status Summary

```
✅ Dockerfile        - Production Ready
✅ openenv.yaml      - Production Ready
✅ inference.py      - Production Ready
✅ README.md         - Production Ready
✅ Integration       - All systems connected
✅ Documentation     - Complete
✅ Testing           - Validated
✅ Deployment        - Ready
```

---

**Last Updated**: April 2, 2026  
**All Files**: ✅ Generated Successfully  
**Status**: 🚀 Ready for Production
