# APEX Advanced Features - Quick Reference Card

**6 Powerful New Features | Production Ready | April 3, 2026**

---

## 🎯 Quick Feature Overview

| Feature | What It Does | Setup Time | Cost | Module |
|---------|-------------|-----------|------|--------|
| 🔧 **WhatsApp** | Send messages, media, templates | 15 min | Pay-per-message | whatsapp_integration.py |
| 🔍 **Web Search** | Search Google/Bing/DuckDuckGo | 0 min (free) | Free or API | search_provider.py |
| 📝 **Summarize** | Summarize text & web pages | 2 min | ~$0.001-0.01 | content_summarizer.py |
| 💻 **Code Gen** | Generate, fix, refactor code | 2 min | ~$0.01-0.05 | code_generator.py |
| ⚡ **Cmd Exec** | Run PowerShell/CMD safely | 1 min | Free | command_executor.py |
| 🐛 **Debug** | Analyze errors, suggest fixes | 2 min | ~$0.01-0.05 | vscode_debugger.py |

---

## 🚀 Get Started in 5 Minutes

### 1. Verify Installation
```bash
cd d:\APEX
python run_server.py
# Server should start without errors
```

### 2. Test Search (No Setup Needed!)
```bash
curl "http://localhost:8000/docs"
# Try a SearchAction in the API
```

### 3. Enable Code Generation (Optional)
```bash
# Ensure OPENAI_API_KEY is in .env
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### 4. Try It!
```python
from apex_env import APEXEnv
from apex_env.models import SearchAction

env = APEXEnv()
obs = env.reset()

action = SearchAction(query="python", num_results=5)
obs, reward, term, trunc, info = env.step(action)
print(f"✅ Search worked! Reward: {reward.total_reward}")
```

---

## 📚 Common Commands

### WhatsApp
```python
whatsapp_manager.send_message("+1234567890", "Hello!")
whatsapp_manager.send_media("+1234567890", "http://...", "image", "Caption")
whatsapp_manager.add_contact("+1234567890", "John")
```

### Search
```python
search_manager.search("python", provider="duckduckgo", num_results=10)
search_manager.image_search("cats")
search_manager.get_status()
```

### Summarize
```python
summarizer_manager.summarize("Your text", style="brief")
summarizer_manager.summarize("https://example.com", style="bullet_points")
```

### Code Gen
```python
code_generator_manager.generate("Create a function that...", "python")
code_generator_manager.fix_bug(code, "Error message", "python")
code_generator_manager.refactor(code, "python")
code_generator_manager.explain(code, "python")
code_generator_manager.generate_tests(code, "python")
```

### Cmd Exec
```python
command_executor_manager.execute("echo hello", "powershell")
command_executor_manager.validate("git pull")
command_executor_manager.execute("pip list", "cmd")
```

### Debug
```python
vscode_debugger_manager.analyze_error(traceback, "python")
vscode_debugger_manager.get_correction(error, code, "python")
vscode_debugger_manager.set_breakpoint("file.py", 10)
```

---

## ⚙️ Configuration (.env Template)

```ini
# ===== OPENAI (For Code Gen, Summarize, Debug) =====
OPENAI_API_KEY=sk-...

# ===== WHATSAPP (Optional) =====
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_id

# ===== GOOGLE SEARCH (Optional) =====
GOOGLE_API_KEY=your_key
GOOGLE_SEARCH_ENGINE_ID=your_id

# ===== BING SEARCH (Optional) =====
BING_SEARCH_KEY=your_key

# Note: DuckDuckGo works without any API key!
```

---

## 🎮 Use in APEX Environment

### Action Types
```python
# WhatsAppAction
WhatsAppAction(phone_number="+...", message="...", media_url=None)

# SearchAction
SearchAction(query="...", num_results=10, provider="google")

# SummarizeAction
SummarizeAction(content="...", style="bullet_points")

# CodeGenAction
CodeGenAction(description="...", language="python", task="generate")

# CommandExecAction
CommandExecAction(command="...", shell="powershell")

# DebugAction
DebugAction(error_text="...", language="python", action="analyze")
```

### Example
```python
from apex_env import APEXEnv
from apex_env.models import CodeGenAction

env = APEXEnv()
obs = env.reset()

# Generate Python code
action = CodeGenAction(
    description="Create a function to validate emails",
    language="python",
    task="generate"
)

obs, reward, terminated, truncated, info = env.step(action)
print(f"Generated code:\n{info['action_result'].details}")
```

---

## ✅ Safety Features

### ✅ Command Execution
- ✅ Dangerous commands blocked
- ✅ Safe commands whitelisted
- ✅ Execution timeout
- ✅ Full logging
- ✅ User confirmation for caution commands

### ✅ Code Generation
- ✅ No code injection
- ✅ Safe API calls
- ✅ Error handling
- ✅ Rate limiting respected

### ✅ Search
- ✅ No data exfiltration
- ✅ Privacy-first (DuckDuckGo option)
- ✅ Safe API calls

---

## 🔐 Integration Points

```
FastAPI Server (http://localhost:8000)
    ↓
APEX Environment (APEXEnv)
    ↓
6 New Action Types (schemas.py)
    ↓
6 Manager Modules (whatsapp, search, summarize, code_gen, cmd_exec, debug)
    ↓
External APIs (OpenAI, Google, Bing, Meta WhatsApp, etc.)
```

---

## 📊 Status Check

```python
from apex_env.whatsapp_integration import whatsapp_manager
from apex_env.search_provider import search_manager
from apex_env.content_summarizer import summarizer_manager
from apex_env.code_generator import code_generator_manager
from apex_env.command_executor import command_executor_manager
from apex_env.vscode_debugger import vscode_debugger_manager

print("WhatsApp:", whatsapp_manager.get_status())
print("Search:", search_manager.get_status())
print("Summarizer:", summarizer_manager.get_status())
print("CodeGen:", code_generator_manager.get_status())
print("CmdExec:", command_executor_manager.get_status())
print("Debugger:", vscode_debugger_manager.get_status())
```

---

## 🎓 Supported Languages (Code Gen)

```
python, javascript, java, c++, go, rust, sql,
typescript, c#, php, swift, kotlin, scala, ruby
```

---

## 🎨 Summary Styles

```
- brief: 1-2 sentences
- detailed: Full comprehensive summary
- bullet_points: 5-10 key points
- executive: C-level format
- key_insights: Main takeaways
```

---

## 📈 Performance & Costs

| Operations | Tokens | Cost | Time |
|-----------|--------|------|------|
| Web search | 100-500 | Free | <1s |
| Code generation | 500-1000 | $0.01-0.05 | 2-5s |
| Summarization | 300-800 | $0.001-0.01 | 2-3s |
| Error analysis | 200-600 | $0.001-0.01 | 1-2s |
| Command exec | 0 | Free | <1s |
| WhatsApp send | 0 | Metered | <2s |

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Check file exists: `ls apex_env/*.py` |
| `WhatsApp not configured` | Add credentials to `.env` |
| `OpenAI error` | Verify `OPENAI_API_KEY` in `.env` |
| `Command blocked` | Use `confirm_risky=False` for safe commands |
| `No search results` | Try different `provider` or keywords |
| `Rate limit` | Add 2-second delay between requests |

---

## 📖 Full Documentation

See: **COMPREHENSIVE_ADVANCED_FEATURES_GUIDE.md** (50+ pages)

---

## 🎯 Next Steps

1. ✅ Verify setup: `python run_server.py`
2. ✅ Test search: Use API at http://localhost:8000/docs
3. ✅ Try code gen: Add `OPENAI_API_KEY` to `.env`
4. ✅ Deploy: Use Docker or cloud platform
5. ✅ Build agents: Use features in RL training

---

**Status: ✅ PRODUCTION READY**

All 6 features tested and integrated!

**Last Updated:** April 3, 2026
