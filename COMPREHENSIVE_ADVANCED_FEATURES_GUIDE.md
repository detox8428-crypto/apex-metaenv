# APEX Advanced Features - Comprehensive Guide

**Date Created:** April 3, 2026  
**APEX Version:** 2.0 with Advanced AI Capabilities  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Feature Summary](#feature-summary)
3. [Architecture](#architecture)
4. [Setup & Configuration](#setup--configuration)
5. [Individual Features](#individual-features)
6. [API Usage Examples](#api-usage-examples)
7. [Integration Guide](#integration-guide)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

APEX now includes **6 powerful AI-enabled features** that extend its capabilities far beyond email and calendar management. These features are:

1. **WhatsApp Messaging** - Send WhatsApp messages via Meta's official API
2. **Web Search** - Search the internet across multiple providers
3. **Content Summarization** - Summarize text and web content
4. **Code Generation & Assistance** - Generate, fix, refactor, and explain code
5. **Secure Command Execution** - Execute system commands safely  
6. **VS Code Debugging** - Analyze errors and provide code corrections

All integrated into the FastAPI backend with full safety, validation, and error handling.

---

## ✨ Feature Summary

### 1. WhatsApp Business API Integration

**What it does:** Sends messages, media, and templates via WhatsApp

**Use Cases:**
- Send automated notifications
- Share media files
- Send template-based messages
- Build WhatsApp bots

**Status:** ✅ Ready to configure  
**Setup Time:** 10-15 minutes  
**Cost:** Based on message volume (Meta pricing)

### 2. Web Search Provider

**What it does:** Search the web across Google, Bing, or DuckDuckGo

**Use Cases:**
- Answer research questions
- Find information programmatically
- Image search
- Multi-source comparison

**Status:** ✅ Works out of the box (DuckDuckGo), optional APIs for Google/Bing  
**Setup Time:** 5-10 minutes (optional)  
**Cost:** Free (DuckDuckGo) or pay-per-query for Google/Bing

### 3. Content Summarization

**What it does:** Summarizes text or web content using OpenAI GPT

**Use Cases:**
- Summarize articles
- Extract key points
- Create executive summaries
- Process long documents

**Formats:** Brief, Detailed, Bullet Points, Executive, Key Insights

**Status:** ✅ Ready (requires OpenAI API)  
**Setup Time:** 2 minutes  
**Cost:** ~$0.001-0.01 per summary

### 4. Code Generation & Assistance

**What it does:** Generate, fix, refactor, explain, and test code

**Task Types:**
- **Generate**: Create code from description
- **Fix**: Debug and fix broken code
- **Refactor**: Improve code quality
- **Explain**: Understand what code does
- **Test**: Generate unit tests
- **Document**: Add documentation

**Languages:** Python, JavaScript, Java, Go, Rust, SQL, C++, etc.

**Status:** ✅ Ready (requires OpenAI API)  
**Setup Time:** 2 minutes  
**Cost:** ~$0.01-0.05 per operation

### 5. Secure Command Execution

**What it does:** Execute PowerShell and Command Prompt commands safely

**Features:**
- Command validation and whitelisting
- Dangerous command blocking
- Execution timeout
- Full output capture
- Security logging

**Status:** ✅ Production ready  
**Setup Time:** 1 minute  
**Cost:** Free

### 6. VS Code Debugging & Code Correction

**What it does:** Analyze errors, suggest fixes, and provide debugging help

**Features:**
- Stack trace parsing
- Error classification
- Root cause analysis
- Correction suggestions
- Breakpoint management

**Status:** ✅ Ready (requires OpenAI API)  
**Setup Time:** 2 minutes  
**Cost:** ~$0.01-0.05 per analysis

---

## 🏗️ Architecture

### Module Structure

```
apex_env/
├── whatsapp_integration.py       # WhatsApp Business API
├── search_provider.py             # Web search (Google/Bing/DuckDuckGo)
├── content_summarizer.py          # Content summarization (OpenAI)
├── code_generator.py              # Code generation & assistance
├── command_executor.py            # Secure command execution
├── vscode_debugger.py            # Error analysis & debugging
├── models/
│   └── schemas.py                # Updated with 6 new Action types
└── environment.py                # Integrated all modules
```

### Action Types

Each feature is represented as an action type in the APEX environment:

```python
# New Action Types in Environment
- WhatsAppAction         # Send WhatsApp messages
- SearchAction          # Search the web
- SummarizeAction       # Summarize content
- CodeGenAction         # Generate/fix/refactor code
- CommandExecAction     # Execute system commands
- DebugAction           # Debug and analyze errors
```

### Flow Diagram

```
Agent Decision
    ↓
[WhatsApp/Search/Summarize/CodeGen/Debug/Command]Action
    ↓
Environment.step()
    ↓
Dispatch to Handler
    ↓
Module Processing (_whatsapp/search/summarize/code_generator/command/vscode_)
    ↓
ActionResult
    ↓
Reward Computation
    ↓
Observation
```

---

## ⚙️ Setup & Configuration

### Prerequisites

```
✅ Python 3.13+
✅ FastAPI 0.104+
✅ Uvicorn 0.24+
✅ All 10 packages installed (already done)
✅ APEX running
```

### Optional API Keys (Add to .env)

Create or update your `.env` file:

```bash
# ============== WHATSAPP ==============
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_biz_account_id

# ============== GOOGLE SEARCH ==============
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# ============== BING SEARCH ==============
BING_SEARCH_KEY=your_bing_api_key

# ============== OPENAI (Required for Code Gen, Summarize, Debug) ==============
OPENAI_API_KEY=your_openai_api_key      # Already have this hopefully!
```

### Quick Setup Commands

**1. Verify All Modules Load**
```bash
cd d:\APEX
python -c "
from apex_env.whatsapp_integration import whatsapp_manager
from apex_env.search_provider import search_manager
from apex_env.content_summarizer import summarizer_manager
from apex_env.code_generator import code_generator_manager
from apex_env.command_executor import command_executor_manager
from apex_env.vscode_debugger import vscode_debugger_manager
print('✅ All modules loaded successfully!')
"
```

**2. Test Individual Modules**
```bash
# Test search (requires no setup)
python -c "from apex_env.search_provider import search_manager; print(search_manager.search('python'))"

# Test command execution
python -c "from apex_env.command_executor import command_executor_manager; print(command_executor_manager.execute('echo hello'))"

# Test code generation
python -c "from apex_env.code_generator import code_generator_manager; print(code_generator_manager.get_status())"
```

---

## 🔧 Individual Features

### 1. WhatsApp Business API

#### Setup Steps

1. **Create Meta Business Account**
   - Go to https://business.facebook.com
   - Create business account
   
2. **Set Up WhatsApp Business API**
   - Navigate to WhatsApp Business
   - Request official API access
   - Complete verification
   - Get credentials:
     - Phone Number ID
     - Access Token
     - Business Account ID

3. **Add to .env**
   ```
   WHATSAPP_PHONE_NUMBER_ID=123456789
   WHATSAPP_ACCESS_TOKEN=your_token_here
   WHATSAPP_BUSINESS_ACCOUNT_ID=your_account_id
   ```

4. **Configure Contacts**
   ```python
   from apex_env.whatsapp_integration import whatsapp_manager
   
   # Add contact
   result = whatsapp_manager.add_contact("+1234567890", "John Doe")
   ```

#### Usage Examples

**Send Text Message**
```python
result = whatsapp_manager.send_message(
    phone_number="+1234567890",
    message="Hello World!"
)
```

**Send Media**
```python
result = whatsapp_manager.send_media(
    phone_number="+1234567890",
    media_url="https://example.com/image.jpg",
    media_type="image",
    caption="Check this out!"
)
```

  
**Send Template**
```python
result = whatsapp_manager.send_template(
    phone_number="+1234567890",
    template_name="hello_world",
    params=["parameter1", "parameter2"]
)
```

#### In APEX Actions

```python
from apex_env.models import WhatsAppAction

action = WhatsAppAction(
    phone_number="+1234567890",
    message="Hello from APEX!",
    use_template=False
)

observation, reward, terminated, truncated, info = env.step(action)
```

---

### 2. Web Search Provider

#### Setup Steps (Optional)

**Using DuckDuckGo (No setup needed!)**
- Already enabled and working
- No API key required
- Free

**Using Google Custom Search**
1. Go to https://programmablesearchengine.google.com
2. Create search engine
3. Get `GOOGLE_SEARCH_ENGINE_ID`
4. Get API key from Google Cloud Console
5. Add to .env:
   ```
   GOOGLE_API_KEY=your_key
   GOOGLE_SEARCH_ENGINE_ID=your_id
   ```

**Using Bing Search**
1. Go to https://www.microsoft.com/en-us/bing/apis
2. Create API subscription
3. Get `BING_SEARCH_KEY`
4. Add to .env

#### Usage Examples

**Simple Search**
```python
from apex_env.search_provider import search_manager

result = search_manager.search("machine learning tutorial", num_results=10)

# Returns:
# {
#     "success": True,
#     "query": "machine learning tutorial",
#     "total": 10,
#     "provider": "duckduckgo",
#     "results": [
#         {
#             "rank": 1,
#             "title": "...",
#             "url": "...",
#             "snippet": "...",
#             "source": "DuckDuckGo",
#             "relevance": 0.95
#         },
#         ...
#     ]
# }
```

**Image Search**
```python
result = search_manager.image_search("cats", num_results=5)
```

**In APEX Actions**
```python
from apex_env.models import SearchAction

action = SearchAction(
    query="python best practices",
    search_type="web",
    num_results=30,
    provider="duckduckgo"  # Optional
)

observation, reward, terminated, truncated, info = env.step(action)
```

---

### 3. Content Summarization

#### Setup Steps

1. **Ensure OpenAI API Key**
   ```
   OPENAI_API_KEY=sk-...
   ```

2. **Install openai library**
   ```bash
   pip install openai>=1.3.0
   ```

#### Usage Examples

**Summarize Text**
```python
from apex_env.content_summarizer import summarizer_manager

result = summarizer_manager.summarize(
    "Your long text here...",
    style="brief"  # brief, detailed, bullet_points, executive, key_insights
)

# Returns: {
#     "success": True,
#     "summary": "Summary text...",
#     "style": "brief",
#     "tokens_used": 150,
#     "cost": 0.0005
# }
```

**Summarize Web Content**
```python
result = summarizer_manager.summarize(
    "https://example.com/article",
    style="executive"
)
```

**Summary Styles**

| Style | Use Case | Example Length |
|-------|----------|-----------------|
| brief | Quick summary | 1-2 sentences |
| detailed | Full summary | 3-5 paragraphs |
| bullet_points | Key points | 5-10 bullets |
| executive | C-level summary | 2-3 paragraphs |
| key_insights | Main takeaways | 5-7 points |

**In APEX Actions**
```python
from apex_env.models import SummarizeAction

action = SummarizeAction(
    content="https://arxiv.org/abs/2301.00000",
    style="bullet_points"
)

observation, reward, terminated, truncated, info = env.step(action)
```

---

### 4. Code Generation & Assistance

#### Setup Steps

1. **Ensure OpenAI API Key**
   ```
   OPENAI_API_KEY=sk-...
   ```

#### Usage Examples

**Generate Code**
```python
from apex_env.code_generator import code_generator_manager

result = code_generator_manager.generate(
    description="Create a function that validates email addresses",
    language="python",
    context="Use regex for validation"
)

# Returns:
# {
#     "success": True,
#     "code": "def validate_email(email):...",
#     "language": "python",
#     "tokens": 250,
#     "cost": 0.001
# }
```

**Fix Bug**
```python
buggy_code = """
def add(a, b)
    return a + b
"""

result = code_generator_manager.fix_bug(
    code=buggy_code,
    issue="Syntax error in function definition",
    language="python"
)

# Returns fixed code and explanation
```

**Refactor Code**
```python
result = code_generator_manager.refactor(
    code="your_code_here",
    language="python",
    goals="Improve readability and performance"
)
```

**Explain Code**
```python
result = code_generator_manager.explain(
    code="print('Hello World')",
    language="python"
)

# Returns detailed explanation
```

**Generate Tests**
```python
result = code_generator_manager.generate_tests(
    code="def add(a, b): return a + b",
    language="python",
    test_framework="pytest"
)

# Returns test code
```

**Supported Languages**
```
python, javascript, java, c++, go, rust, sql, 
typescript, c#, php, swift, kotlin, scala, ruby
```

**In APEX Actions**
```python
from apex_env.models import CodeGenAction

action = CodeGenAction(
    description="Fix this broken function",
    language="python",
    task="fix",
    code="def broken():\n    return 1 +\n"
)

observation, reward, terminated, truncated, info = env.step(action)
```

---

### 5. Secure Command Execution

#### Features

✅ **Safe by default** - Dangerous commands blocked  
✅ **Validation** - Commands checked before execution  
✅ **Whitelisting** - Safe commands pre-approved  
✅ **Timeout** - Commands stop after max time  
✅ **Logging** - Full execution history  

#### Safe Commands

Pre-approved safe commands include:
```
get-childitem, ls, dir, cat, type
python, node, npm, pip, git
curl, wget, ping, nslookup
docker, kubectl, dotnet
systeminfo, whoami, date, time
```

#### Dangerous Commands (Blocked)

Blocked commands include:
```
del, rm, rmdir, format
reg, regedit, chmod, chown
net user, shutdown, reboot
iptables, netsh, /dev/
drop database, truncate
```

#### Usage Examples

**Execute Safe Command**
```python
from apex_env.command_executor import command_executor_manager

# Safe command - executes without confirmation
result = command_executor_manager.execute(
    command="echo Hello World",
    shell="powershell",
    timeout_seconds=30
)

# Returns:
# {
#     "success": True,
#     "stdout": "Hello World\n",
#     "stderr": "",
#     "return_code": 0,
#     "execution_time": 0.05,
#     "command_type": "safe"
# }
```

**Execute Caution Command (Requires Confirmation)**
```python
result = command_executor_manager.execute(
    command="pip install numpy",
    shell="powershell",
    confirm_risky=True
)

# Returns:
# {
#     "success": False,
#     "requires_confirmation": True,
#     "command_type": "caution",
#     "reason": "Unknown command - requires caution"
# }
```

**Execute Batch Commands**
```python
results = command_executor_manager.powershell_executor.execute_batch([
    "echo Starting",
    "python --version",
    "pip list",
])
```

**Validate Command**
```python
validation = command_executor_manager.validate("git pull")

# Returns:
# {
#     "command": "git pull",
#     "type": "safe",
#     "safe": True,
#     "reason": "Whitelisted safe command"
# }
```

**In APEX Actions**
```python
from apex_env.models import CommandExecAction

action = CommandExecAction(
    command="python -c \"print('APEX')\"",
    shell="powershell",
    timeout_seconds=30,
    require_confirmation=False
)

observation, reward, terminated, truncated, info = env.step(action)
```

---

### 6. VS Code Debugger & Error Correction

#### Features

✅ **Stack Trace Parsing** - Understand Python and JavaScript errors  
✅ **Error Classification** - Identify error type  
✅ **Root Cause Analysis** - Understand why error happened  
✅ **Correction Suggestions** - Get fix recommendations  
✅ **Breakpoint Management** - Set and manage breakpoints  

#### Supported Error Types

```
SYNTAX - Syntax errors
RUNTIME - Runtime errors
LOGIC - Logic errors
TYPE - Type mismatches
NULL_REFERENCE - Undefined/null access
INDEX_OUT_OF_BOUNDS - Array index error
KEY_ERROR - Dictionary key missing
IMPORT_ERROR - Module not found
PERMISSION_ERROR - Access denied
IO_ERROR - File I/O errors
```

#### Usage Examples

**Analyze Error**
```python
from apex_env.vscode_debugger import vscode_debugger_manager

error_text = """
Traceback (most recent call last):
  File "app.py", line 10, in <module>
    result = calculate(x)
  File "app.py", line 5, in calculate
    return data['value']  # KeyError!
KeyError: 'value'
"""

analysis = vscode_debugger_manager.analyze_error(error_text, language="python")

# Returns:
# {
#     "success": True,
#     "parsed_error": {
#         "error_type": "key_error",
#         "error_message": "'value'",
#         "stack_frames": [...],
#         "frame_count": 2
#     },
#     "diagnosis": {
#         "likely_cause": "Dictionary key doesn't exist",
#         "suggestions": [
#             "Check if key exists before access",
#             "Use .get() with default value"
#         ],
#         "common_fix": "Use .get() method or add key check"
#     }
# }
```

**Get Correction**
```python
buggy_code = """
def process_user(user):
    return user['name'].upper()  # What if user doesn't have 'name'?
"""

correction = vscode_debugger_manager.get_correction(
    error_text="KeyError: 'name'",
    code=buggy_code,
    language="python"
)

# Returns:
# {
#     "success": True,
#     "error_type": "key_error",
#     "correction": "Fixed code with explanation...",
#     "tokens_used": 300,
# }
```

**Set Breakpoint**
```python
bp = vscode_debugger_manager.set_breakpoint(
    file="app.py",
    line=10,
    condition="x > 0"
)
```

**In APEX Actions**
```python
from apex_env.models import DebugAction

action = DebugAction(
    error_text="KeyError: 'name'",
    language="python",
    action="analyze",
    code="return data['name']"
)

observation, reward, terminated, truncated, info = env.step(action)
```

---

## 🚀 API Usage Examples

### Complete Example: Multi-Feature Workflow

```python
from apex_env import APEXEnv
from apex_env.models import (
    SearchAction, SummarizeAction, CodeGenAction, DebugAction, CommandExecAction, WhatsAppAction
)

# Initialize environment
env = APEXEnv()
obs = env.reset()

# 1. Search for information
search_action = SearchAction(query="python best practices 2024", num_results=5)
obs, reward, term, trunc, info = env.step(search_action)
print(f"Search reward: {reward.total_reward:.3f}")

# 2. Summarize first result
summarize_action = SummarizeAction(
    content="https://example.com/article",
    style="bullet_points"
)
obs, reward, term, trunc, info = env.step(summarize_action)
print(f"Summarize reward: {reward.total_reward:.3f}")

# 3. Generate example code
code_action = CodeGenAction(
    description="Generate a REST API endpoint",
    language="python",
    task="generate",
    context="Using FastAPI",
)
obs, reward, term, trunc, info = env.step(code_action)
print(f"Code gen reward: {reward.total_reward:.3f}")

# 4. Debug some code
debug_action = DebugAction(
    error_text="TypeError: string indices must be integers",
    language="python",
    action="analyze",
    code="result = data[0]['name']"
)
obs, reward, term, trunc, info = env.step(debug_action)
print(f"Debug reward: {reward.total_reward:.3f}")

# 5. Execute command
cmd_action = CommandExecAction(
    command="python --version",
    shell="powershell"
)
obs, reward, term, trunc, info = env.step(cmd_action)
print(f"Command reward: {reward.total_reward:.3f}")

# 6. Send WhatsApp (if configured)
if env.state.whatsapp_enabled:
    wa_action = WhatsAppAction(
        phone_number="+1234567890",
        message="Workflow complete!"
    )
    obs, reward, term, trunc, info = env.step(wa_action)
    print(f"WhatsApp reward: {reward.total_reward:.3f}")
```

---

## 🔌 Integration Guide

### How Modules Are Integrated

Each feature follows this pattern:

1. **Module Creation** - Implements manager class
2. **Schema Definition** - Pydantic model for action
3. **Environment Dispatch** - step() method routes to handler
4. **Handler Implementation** - _process_XXX_action() method
5. **Reward Computation** - Contributes to reward signal

### Adding New Features

To add more features:

1. **Create Module** (`apex_env/new_feature.py`)
   ```python
   class NewFeatureManager:
       def __init__(self):
           self.enabled = True  # or check for API key
       
       def do_something(self, param):
           # Implementation
           return {"success": True, "result": "..."}
   ```

2. **Add Schema** (in `schemas.py`)
   ```python
   class NewFeatureAction(BaseModel):
       type: str = "new_feature"
       param1: str
       param2: int
   ```

3. **Add to Union** (in `schemas.py`)
   ```python
   Action = Union[..., NewFeatureAction]
   ```

4. **Add Handler** (in `environment.py`)
   ```python
   def _process_new_feature_action(self, action):
       result = feature_manager.do_something(action.param1)
       return ActionResult(...)
   ```

5. **Add Dispatch** (in `environment.py` step method)
   ```python
   elif isinstance(action, NewFeatureAction):
       result = self._process_new_feature_action(action)
   ```

---

## 🐛 Troubleshooting

### Module Import Errors

**Problem:** `ImportError: No module named 'apex_env.whatsapp_integration'`

**Solution:**
```bash
# Verify file exists
ls -la d:\APEX\apex_env\whatsapp_integration.py

# Reload Python path
cd d:\APEX
python -c "import apex_env.whatsapp_integration as w; print(w.__doc__)"
```

### API Key Errors

**Problem:** `WhatsApp not configured` or `Code Generator disabled`

**Solution:**
```bash
# Check .env file
cat .env

# Add missing keys:
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
# etc
```

### OpenAI Rate Limiting

**Problem:** `RateLimitError: Rate limit exceeded`

**Solution:**
```python
# Add delay between requests
import time
time.sleep(2)  # Wait 2 seconds

# Or use try-except
try:
    result = code_generator_manager.generate(...)
except Exception as e:
    print(f"Rate limit, retrying...")
```

### Command Execution Blocked

**Problem:** `Command blocked as dangerous: del /S`

**Solution:**
```python
# Use confirm_risky=False ONLY for trusted commands
result = command_executor_manager.execute(
    "git pull",
    confirm_risky=False  # Safe command, proceed
)

# Or validate first
validation = command_executor_manager.validate("your command")
if validation["safe"]:
    #Execute with confidence
    pass
```

### Search No Results

**Problem:** `No results found` for a valid search

**Solution:**
```python
# Try different provider
result = search_manager.search("query", provider="google")

# Try different keywords
result = search_manager.search("more specific query")

# Check status
print(search_manager.get_status())
```

---

## 📊 Status Dashboard

Check status of all systems:

```python
from apex_env import APEXEnv

env = APEXEnv()

# Check each module
from apex_env.whatsapp_integration import whatsapp_manager
from apex_env.search_provider import search_manager
from apex_env.content_summarizer import summarizer_manager
from apex_env.code_generator import code_generator_manager
from apex_env.command_executor import command_executor_manager
from apex_env.vscode_debugger import vscode_debugger_manager

print("=== APEX Advanced Features Status ===")
print(f"WhatsApp: {whatsapp_manager.get_status()}")
print(f"Search: {search_manager.get_status()}")
print(f"Summarizer: {summarizer_manager.get_status()}")
print(f"Code Generator: {code_generator_manager.get_status()}")
print(f"Command Executor: {command_executor_manager.get_status()}")
print(f"Debugger: {vscode_debugger_manager.get_status()}")
```

---

## 🎓 Learning Resources

### Quick Start (5 minutes)

1. Start server: `python run_server.py`
2. Open API docs: http://localhost:8000/docs
3. Try a search action
4. Check the reward

### Deep Dive (30 minutes)

1. Read this entire guide
2. Try each feature individually
3. Check the module docstrings
4. Try the multi-feature example

### Production Deployment (1-2 hours)

1. Set up all API keys
2. Configure WhatsApp Business API
3. Set up CI/CD pipeline
4. Deploy to Docker
5. Set up monitoring

---

## ✅ Verification Checklist

Before considering setup complete:

- [ ] All 6 module files exist in `apex_env/`
- [ ] Imports work: `python -c "from apex_env.whatsapp_integration import ..."`
- [ ] Schemas updated with 6 new action types
- [ ] Environment.py imports all 6 modules
- [ ] Step method dispatches to all 6 handlers
- [ ] Search works without setup (DuckDuckGo)
- [ ] Command execution works
- [ ] API server starts: `python run_server.py`
- [ ] At least one advanced feature is configured (Code Gen or Search recommended)

---

## 🚀 Next Steps

1. **Choose Your Path:**
   - **Quick Start:** Test search (needs no setup)
   - **AI-Powered:** Set up OpenAI for code gen + summarization
   - **Messaging:** Configure WhatsApp Business API
   - **Execute:** Start running system commands safely

2. **Try in APEX:**
   ```python
   from apex_env import APEXEnv
   from apex_env.models import SearchAction
   
   env = APEXEnv()
   obs = env.reset()
   
   action = SearchAction(query="python tutorials")
   obs, reward, term, trunc, info = env.step(action)
   print(info)  # See result
   ```

3. **Explore API:**
   - Start server: `python run_server.py`
   - Open http://localhost:8000/docs
   - Try new endpoints

4. **Build Custom Agents:**
   - Combine features in workflows
   - Train RL agents on these actions
   - Deploy to production

---

## 📞 Support

For issues:
1. Check the module docstrings
2. Review this guide
3. Check error messages
4. Validate API keys
5. Check logs in `run_server.py`

---

**Status: ✅ PRODUCTION READY**

All features tested and verified. Ready for integration and deployment!

Last updated: April 3, 2026
