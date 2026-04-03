"""
APEX ENVIRONMENT - FASTAPI SERVER SETUP & USAGE GUIDE

Complete guide for setting up and using the FastAPI server.
"""

# ============================================================================
# QUICK START
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                           QUICK START (5 MIN)                            ║
╚════════════════════════════════════════════════════════════════════════════╝

STEP 1: Install dependencies
───────────────────────────

pip install -r requirements.txt

Required packages:
  ├─ fastapi>=0.104.0 ........... Web framework
  ├─ uvicorn>=0.24.0 ............ ASGI server
  ├─ pydantic>=2.0.0 ............ Data validation
  ├─ requests>=2.31.0 ........... HTTP client (for examples)
  └─ python-dateutil>=2.8.0 ..... Date handling


STEP 2: Start the server
────────────────────────

python server.py

Expected output:
  INFO:     Started server process [PID]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:0000

The server is now running on http://localhost:8000


STEP 3: Try it out (in another terminal)
─────────────────────────────────────────

python client_example.py

This will run 7 example scenarios demonstrating:
  1. Health check
  2. Reset and state retrieval
  3. Simple email task
  4. Meeting task
  5. Multilingual workflow
  6. Multiple steps with tracking
  7. Error handling


STEP 4: View interactive documentation
──────────────────────────────────────

Open browser: http://localhost:8000/docs

You can:
  ├─ View all endpoints
  ├─ Test endpoints interactively
  ├─ See request/response examples
  └─ Read parameter documentation
"""

# ============================================================================
# ENDPOINTS REFERENCE
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         ENDPOINTS REFERENCE                              ║
╚════════════════════════════════════════════════════════════════════════════╝


1. GET /health
──────────────

Health check endpoint

Request:
  curl http://localhost:8000/health

Response:
  {
    "status": "healthy",
    "environment_initialized": false,
    "timestamp": "2026-04-02T10:30:45.123456Z"
  }

Use case: Check if server is running and ready


2. POST /reset
──────────────

Reset environment to initial state

Request:
  curl -X POST http://localhost:8000/reset \\
    -H "Content-Type: application/json" \\
    -d '{
      "seed": 42,
      "max_episode_steps": 100
    }'

Parameters:
  ├─ seed (int, optional): Random seed for reproducibility
  └─ max_episode_steps (int): Maximum steps per episode (default: 100)

Response:
  {
    "status": "success",
    "initial_observation": {...},
    "message": "Environment reset to initial state"
  }

Use case: Start new episode with fresh environment


3. POST /step
─────────────

Execute one step in the environment

Request:
  curl -X POST http://localhost:8000/step \\
    -H "Content-Type: application/json" \\
    -d '{
      "action": {
        "action_type": "email",
        "recipient_id": 0,
        "subject": "Test",
        "body": "Test email",
        "language": "EN"
      }
    }'

Action Types:
  
  a) EMAIL ACTION:
     {
       "action_type": "email",
       "recipient_id": 0,
       "subject": "Subject text",
       "body": "Email body",
       "priority": "MEDIUM",
       "language": "EN",
       "cc": [1, 2],
       "bcc": [3]
     }
  
  b) MEETING ACTION:
     {
       "action_type": "meeting",
       "title": "Meeting title",
       "attendee_ids": [0, 1, 2],
       "scheduled_time": "2026-04-05T14:00:00Z",
       "duration_minutes": 60,
       "meeting_type": "VIRTUAL",
       "location": "Room 101",
       "description": "Meeting details"
     }
  
  c) TRANSLATION ACTION:
     {
       "action_type": "translation",
       "text": "Text to translate",
       "source_language": "EN",
       "target_language": "ES"
     }
  
  d) GESTURE ACTION:
     {
       "action_type": "gesture",
       "gesture_code": "SWIPE_LEFT",
       "intensity": 1.0,
       "metadata": {...}
     }
  
  e) NOOP ACTION:
     {
       "action_type": "noop",
       "reason": "Waiting for feedback"
     }

Response:
  {
    "observation": {...},
    "reward": 0.5,
    "done": false,
    "truncated": false,
    "info": {
      "step_count": 1,
      "action_result": {...}
    },
    "timestamp": "2026-04-02T10:31:05.123456Z"
  }

Use case: Execute action and get results


4. GET /state
─────────────

Get current environment state

Request:
  curl http://localhost:8000/state

Response:
  {
    "timestamp": "2026-04-02T10:31:15.123456Z",
    "step_count": 2,
    "episode_reward": 0.75,
    "state": {
      "email_system": {
        "sent_count": 1,
        "pending_count": 0,
        "failed_count": 0
      },
      "calendar": {
        "meeting_count": 0
      },
      "contacts": {
        "contact_count": 150
      },
      "tasks": {
        "total_tasks": 1
      },
      "language_state": {
        "current_language": "EN",
        "detected_language": "EN"
      },
      "gesture_state": {
        "last_gesture": null
      }
    }
  }

Use case: Monitor environment state between steps


5. POST /task
──────────────

Set a task for the environment

Request:
  curl -X POST http://localhost:8000/task \\
    -H "Content-Type: application/json" \\
    -d '{
      "task_type": "email",
      "task_data": {
        "recipient_id": 0,
        "subject": "Project Update",
        "body": "status report",
        "language": "EN"
      }
    }'

Task Types:

  a) EMAIL TASK:
     {
       "task_type": "email",
       "task_data": {
         "recipient_id": 0,
         "subject": "Required subject",
         "body": "Required body content",
         "language": "EN"
       }
     }
  
  b) MEETING TASK:
     {
       "task_type": "meeting",
       "task_data": {
         "attendee_ids": [0, 1, 2],
         "target_date": "2026-04-05T00:00:00Z",
         "time_window": [9, 17],
         "duration_minutes": 60,
         "meeting_type": "VIRTUAL",
         "title": "Meeting name"
       }
     }
  
  c) WORKFLOW TASK:
     {
       "task_type": "workflow",
       "task_data": {
         "input_text": "Text to process",
         "input_language": "EN",
         "target_language": "ES",
         "recipient_id": 0,
         "meeting_attendee_ids": [0, 1]
       }
     }

Response:
  {
    "status": "success",
    "task_name": "Send Email",
    "instruction": "Send an email to contact 0...",
    "difficulty": "easy"
  }

Use case: Define what the agent should accomplish


6. POST /evaluate
──────────────────

Evaluate current state with a grader

Request:
  curl -X POST http://localhost:8000/evaluate \\
    -H "Content-Type: application/json" \\
    -d '{
      "grader_type": "email",
      "task_data": {
        "expected_recipient_id": 0,
        "expected_subject": "Project Update",
        "expected_body": "status report",
        "expected_language": "EN"
      }
    }'

Grader Types:

  a) EMAIL GRADER:
     {
       "grader_type": "email",
       "task_data": {
         "expected_recipient_id": 0,
         "expected_subject": "Subject",
         "expected_body": "Body content",
         "expected_language": "EN"
       }
     }
  
  b) MEETING GRADER:
     {
       "grader_type": "meeting",
       "task_data": {
         "expected_date": "2026-04-05T00:00:00Z",
         "expected_time_window": [9, 17],
         "expected_attendee_ids": [0, 1, 2],
         "expected_duration": 60,
         "expected_meeting_type": "VIRTUAL",
         "tolerance_minutes": 15
       }
     }
  
  c) WORKFLOW GRADER:
     {
       "grader_type": "workflow",
       "task_data": {
         "steps": ["translate", "email", "meeting"],
         "step_1_data": {...},
         "step_2_data": {...},
         "step_3_data": {...}
       }
     }

Response:
  {
    "score": 0.85,
    "success": true,
    "feedback": "Detailed evaluation breakdown...",
    "timestamp": "2026-04-02T10:31:25.123456Z"
  }

Use case: Measure how well the agent completed the task
"""

# ============================================================================
# COMPLETE WORKFLOW EXAMPLE
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    COMPLETE WORKFLOW EXAMPLE                             ║
╚════════════════════════════════════════════════════════════════════════════╝


SCENARIO: Agent performs an email task

STEP 1: Health check
────────────────────

GET http://localhost:8000/health

Response:
{
  "status": "healthy",
  "environment_initialized": false,
  "timestamp": "2026-04-02T10:30:00Z"
}


STEP 2: Reset environment
──────────────────────────

POST http://localhost:8000/reset
Content-Type: application/json

{
  "seed": 42,
  "max_episode_steps": 10
}

Response:
{
  "status": "success",
  "initial_observation": {...},
  "message": "Environment reset to initial state"
}


STEP 3: Set task
────────────────

POST http://localhost:8000/task
Content-Type: application/json

{
  "task_type": "email",
  "task_data": {
    "recipient_id": 0,
    "subject": "Meeting Request",
    "body": "schedule a meeting",
    "language": "EN"
  }
}

Response:
{
  "status": "success",
  "task_name": "Send Email",
  "instruction": "Send an email to contact 0 about 'Meeting Request'...",
  "difficulty": "easy"
}


STEP 4: Execute action
──────────────────────

POST http://localhost:8000/step
Content-Type: application/json

{
  "action": {
    "action_type": "email",
    "recipient_id": 0,
    "subject": "Meeting Request for Tomorrow",
    "body": "I would like to schedule a meeting tomorrow.",
    "language": "EN"
  }
}

Response:
{
  "observation": {...},
  "reward": 0.2,
  "done": false,
  "truncated": false,
  "info": {
    "step_count": 1,
    "action_result": {
      "success": true,
      "message": "Email sent successfully"
    }
  },
  "timestamp": "2026-04-02T10:30:30Z"
}


STEP 5: Get state
──────────────────

GET http://localhost:8000/state

Response:
{
  "timestamp": "2026-04-02T10:30:45Z",
  "step_count": 1,
  "episode_reward": 0.2,
  "state": {
    "email_system": {
      "sent_count": 1,
      "pending_count": 0,
      "failed_count": 0
    },
    ...
  }
}


STEP 6: Evaluate
────────────────

POST http://localhost:8000/evaluate
Content-Type: application/json

{
  "grader_type": "email",
  "task_data": {
    "expected_recipient_id": 0,
    "expected_subject": "Meeting Request",
    "expected_body": "schedule meeting",
    "expected_language": "EN"
  }
}

Response:
{
  "score": 0.85,
  "success": true,
  "feedback": "✓ Recipient match: 0.30/0.30\\n✓ Subject: 0.225/0.25\\n...",
  "timestamp": "2026-04-02T10:31:00Z"
}

Score 0.85 >= threshold 0.75 → TASK SUCCESS!
"""

# ============================================================================
# PYTHON CLIENT USAGE
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                   PYTHON CLIENT USAGE EXAMPLES                           ║
╚════════════════════════════════════════════════════════════════════════════╝


BASIC EXAMPLE:
──────────────

from client_example import APEXClient

client = APEXClient("http://localhost:8000")

# Reset
client.reset(seed=42)

# Set task
client.set_task("email", {
    "recipient_id": 0,
    "subject": "Test",
    "body": "test",
})

# Execute action
response = client.step({
    "action_type": "email",
    "recipient_id": 0,
    "subject": "Test Email",
    "body": "test email content",
})

# Get state
state = client.get_state()
print(f"Emails sent: {state['state']['email_system']['sent_count']}")

# Evaluate
evaluation = client.evaluate("email", {
    "expected_recipient_id": 0,
    "expected_subject": "Test",
    "expected_body": "test",
})

print(f"Score: {evaluation['score']:.2f}")
print(f"Success: {evaluation['success']}")

client.close()


TRAINING LOOP EXAMPLE:
──────────────────────

from client_example import APEXClient
import random

client = APEXClient("http://localhost:8000")

# Training parameters
num_episodes = 100
actions_per_episode = 10

total_reward = 0

for episode in range(num_episodes):
    # Reset for new episode
    client.reset(seed=episode)
    
    # Random actions for demonstration
    for step in range(actions_per_episode):
        action = {
            "action_type": "email",
            "recipient_id": random.randint(0, 5),
            "subject": f"Email {step}",
            "body": f"Content {step}",
        }
        
        response = client.step(action)
        reward = response['reward']
        total_reward += reward
        
        if response['done'] or response['truncated']:
            break
    
    # Print progress
    if (episode + 1) % 10 == 0:
        print(f"Episode {episode + 1}/{num_episodes}, Avg reward: {total_reward / (episode + 1):.3f}")

client.close()
"""

# ============================================================================
# CURL EXAMPLES
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         CURL EXAMPLES                                    ║
╚════════════════════════════════════════════════════════════════════════════╝


1. Health Check
───────────────

curl http://localhost:8000/health | jq


2. Reset Environment
────────────────────

curl -X POST http://localhost:8000/reset \\
  -H "Content-Type: application/json" \\
  -d '{"seed": 42, "max_episode_steps": 100}' | jq


3. Send Email
─────────────

curl -X POST http://localhost:8000/step \\
  -H "Content-Type: application/json" \\
  -d '{
    "action": {
      "action_type": "email",
      "recipient_id": 0,
      "subject": "Test",
      "body": "test content",
      "language": "EN"
    }
  }' | jq


4. Get State
────────────

curl http://localhost:8000/state | jq


5. Set Email Task
──────────────────

curl -X POST http://localhost:8000/task \\
  -H "Content-Type: application/json" \\
  -d '{
    "task_type": "email",
    "task_data": {
      "recipient_id": 0,
      "subject": "Test",
      "body": "content"
    }
  }' | jq


6. Evaluate with Grader
────────────────────────

curl -X POST http://localhost:8000/evaluate \\
  -H "Content-Type: application/json" \\
  -d '{
    "grader_type": "email",
    "task_data": {
      "expected_recipient_id": 0,
      "expected_subject": "Test",
      "expected_body": "content"
    }
  }' | jq
"""

# ============================================================================
# CONFIGURATION & DEPLOYMENT
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                 CONFIGURATION & DEPLOYMENT GUIDE                         ║
╚════════════════════════════════════════════════════════════════════════════╝


RUNNING SERVER WITH CUSTOM SETTINGS:
────────────────────────────────────

#!/usr/bin/env python
import uvicorn
from server import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,  # Disable auto-reload for production
        workers=4,     # Use 4 worker processes
    )


ENVIRONMENT VARIABLES:
──────────────────────

# Create .env file
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
WORKERS=4


DOCKER DEPLOYMENT:
──────────────────

# Dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "server.py"]

# Build and run
docker build -t apex-env .
docker run -p 8000:8000 apex-env


NGINX REVERSE PROXY:
────────────────────

# /etc/nginx/sites-available/apex
server {
    listen 80;
    server_name apex-api.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}


SYSTEMD SERVICE:
────────────────

# /etc/systemd/system/apex-env.service
[Unit]
Description=APEX Environment API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/www-data/apex
ExecStart=/usr/bin/python3 server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable apex-env
sudo systemctl start apex-env
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        TROUBLESHOOTING                                   ║
╚════════════════════════════════════════════════════════════════════════════╝


PROBLEM                          SOLUTION
────────────────────────────────────────────────────────────────────────────

Server won't start                Check port 8000 is available:
  "Address already in use"           lsof -i :8000
                                  Or specify different port:
                                     uvicorn server:app --port 8001

Connection refused                Ensure server is running:
  "Failed to connect"                python server.py
                                  Check firewall allowing port 8000

Action validation fails            Review action_type and parameters
  "Invalid action"                   See ENDPOINTS REFERENCE above
                                  Verify payload JSON is valid

Step before reset                 Always call /reset before /step
  "Environment not initialized"      POST /reset

Module not found                  Install dependencies:
  "ModuleNotFoundError"              pip install -r requirements.txt

Timestamp errors                  Use ISO format with Z suffix:
  "Invalid datetime"                 "2026-04-05T14:00:00Z"

Import errors                     Ensure apex_env package is in path:
  "Cannot import apex_env"           export PYTHONPATH=/path/to/apex
                                  Or install in development:
                                     cd /path/to/apex
                                     pip install -e .

Out of memory                     Environment stores full history
  "MemoryError"                      Call /reset to free memory
                                  Use smaller max_episode_steps

Port already bound                Find and kill process using port:
  "Address already in use"           Windows: netstat -ano | findstr :8000
                                  Linux: sudo lsof -i :8000 | grep LISTEN
                                         sudo kill -9 PID

For more help:                    Check logs in console output
  Review server logs              Run with verbose logging:
                                     python server.py --log-level debug
"""

# ============================================================================
# API DOCUMENTATION
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════════╗
║                   AUTO-GENERATED API DOCUMENTATION                       ║
╚════════════════════════════════════════════════════════════════════════════╝

FastAPI automatically generates interactive API documentation.

Access it at:
  ├─ http://localhost:8000/docs (Swagger UI)
  ├─ http://localhost:8000/redoc (ReDoc)
  └─ http://localhost:8000/openapi.json (OpenAPI spec)

The Swagger UI provides:
  ✓ All endpoints listed with descriptions
  ✓ Request/response schema visualization
  ✓ Interactive testing of endpoints
  ✓ Parameter documentation
  ✓ Try it out buttons for each endpoint
"""

if __name__ == "__main__":
    print(__doc__)
