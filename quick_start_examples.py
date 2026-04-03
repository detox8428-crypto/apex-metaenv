#!/usr/bin/env python
"""
APEX Advanced Features - Quick Start Examples

This script shows practical examples of using each of the 6 new features.
Copy and modify these examples for your own use cases.

Usage:
    python quick_start_examples.py
"""

import os
from apex_env import APEXEnv
from apex_env.models import (
    SearchAction, SummarizeAction, CodeGenAction,
    CommandExecAction, DebugAction, WhatsAppAction
)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_result(action_name, result):
    """Print action result nicely"""
    print(f"📊 Result from {action_name}:")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    if result.details:
        print(f"   Details: {result.details}")
    print()

def example_1_web_search():
    """Example 1: Search the web for information"""
    print_section("Example 1: 🔍 Web Search (NO SETUP REQUIRED!)")
    
    print("This works immediately with DuckDuckGo - no API keys needed!")
    print("Optional: Add GOOGLE_API_KEY or BING_SEARCH_KEY for better results\n")
    
    env = APEXEnv()
    env.reset()
    
    # Search for information
    action = SearchAction(
        query="Python asyncio tutorial",
        num_results=5,
        search_type="web"
    )
    
    print(f"🔎 Searching for: '{action.query}'")
    obs, reward, term, trunc, info = env.step(action)
    
    result = info['action_result']
    print_result("Search", result)
    
    if result.details and 'results' in result.details:
        print("Top results:")
        for i, item in enumerate(result.details['results'][:3], 1):
            print(f"  {i}. {item.title}")
            print(f"     {item.snippet[:80]}...")
            print()

def example_2_image_search():
    """Example 2: Search for images"""
    print_section("Example 2: 🖼️ Image Search")
    
    env = APEXEnv()
    env.reset()
    
    # Search for images
    action = SearchAction(
        query="space nebula",
        search_type="image",
        num_results=5
    )
    
    print(f"🔎 Searching for images: '{action.query}'")
    obs, reward, term, trunc, info = env.step(action)
    
    result = info['action_result']
    print_result("Image Search", result)

def example_3_summarize_text():
    """Example 3: Summarize text content"""
    print_section("Example 3: 📝 Summarize Text (Requires OPENAI_API_KEY)")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not configured. Skipping this example.")
        print("Configure it in .env to enable this feature.\n")
        return
    
    env = APEXEnv()
    env.reset()
    
    # Sample text to summarize
    long_text = """
    Machine learning is a subset of artificial intelligence (AI) that provides systems 
    the ability to automatically learn and improve from experience without being explicitly 
    programmed. Machine learning focuses on the development of computer programs that can 
    access data and use it to learn for themselves. The process of learning begins with 
    observations or data, such as examples, direct experience, or instruction, in order to 
    look for patterns in data and make better decisions in the future based on the examples 
    that we provide. The primary aim is to allow the computers to learn automatically without 
    human intervention or assistance and adjust actions accordingly.
    """
    
    # Summarize in brief style
    action = SummarizeAction(
        content=long_text,
        style="brief",
        max_length=100
    )
    
    print(f"📄 Original text ({len(long_text)} chars)")
    print(f"✨ Summarizing in 'brief' style...\n")
    
    obs, reward, term, trunc, info = env.step(action)
    result = info['action_result']
    print_result("Summarization", result)
    
    if result.details and 'summary' in result.details:
        print(f"Summary:\n{result.details['summary']}\n")

def example_4_summarize_url():
    """Example 4: Summarize a web article"""
    print_section("Example 4: 🌐 Summarize Web Content (Requires OPENAI_API_KEY)")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not configured. Skipping this example.")
        print("Configure it in .env to enable this feature.\n")
        return
    
    env = APEXEnv()
    env.reset()
    
    # Summarize article (in real use, provide actual URL or extracted text)
    action = SummarizeAction(
        content="https://example.com/article",  # In practice, use real URL
        style="executive",  # Executive summary style
    )
    
    print(f"📰 Summarizing web content in 'executive' style...\n")
    print("Note: In production, provide actual article URLs or content\n")

def example_5_generate_code():
    """Example 5: Generate code"""
    print_section("Example 5: 💻 Generate Code (Requires OPENAI_API_KEY)")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not configured. Skipping this example.")
        print("Configure it in .env to enable this feature.\n")
        return
    
    env = APEXEnv()
    env.reset()
    
    # Generate code
    action = CodeGenAction(
        description="Function to validate email addresses",
        language="python",
        task="generate"
    )
    
    print(f"🤖 Generating {action.language} code...")
    print(f"   Task: {action.task}")
    print(f"   Description: {action.description}\n")
    
    obs, reward, term, trunc, info = env.step(action)
    result = info['action_result']
    print_result("Code Generation", result)
    
    if result.details and 'code' in result.details:
        print(f"Generated Code:\n```{action.language}\n{result.details['code']}\n```\n")

def example_6_fix_code():
    """Example 6: Fix buggy code"""
    print_section("Example 6: 🔧 Fix Code (Requires OPENAI_API_KEY)")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not configured. Skipping this example.")
        print("Configure it in .env to enable this feature.\n")
        return
    
    env = APEXEnv()
    env.reset()
    
    # Buggy code to fix
    buggy_code = """
def calculate_average(numbers):
    total = sum(numbers)
    average = total / len(numbers)  # Bug: doesn't handle empty list
    return average
    """
    
    action = CodeGenAction(
        description="Fix division by zero error when list is empty",
        language="python",
        task="fix",
        code=buggy_code
    )
    
    print(f"🐛 Fixing Python code...\n")
    print(f"Original (buggy):\n{buggy_code}\n")
    
    obs, reward, term, trunc, info = env.step(action)
    result = info['action_result']
    print_result("Code Fixing", result)

def example_7_execute_command():
    """Example 7: Execute safe system commands"""
    print_section("Example 7: ⚙️ Execute Commands (PowerShell/CMD)")
    
    env = APEXEnv()
    env.reset()
    
    # Safe command - get Python version
    action = CommandExecAction(
        command="python --version",
        shell="powershell",
        timeout_seconds=10,
        require_confirmation=False
    )
    
    print(f"💻 Executing: {action.command}\n")
    
    obs, reward, term, trunc, info = env.step(action)
    result = info['action_result']
    print_result("Command Execution", result)
    
    if result.details:
        print(f"Output: {result.details.get('stdout', 'No output')}\n")

def example_8_list_files():
    """Example 8: List files safely"""
    print_section("Example 8: 📁 List Files")
    
    env = APEXEnv()
    env.reset()
    
    # Safe command - list files
    action = CommandExecAction(
        command="dir /B",  # or "ls -la" on unix
        shell="cmd",
        timeout_seconds=10,
        require_confirmation=False,
        working_dir="."
    )
    
    print(f"📂 Listing files in current directory...\n")
    
    obs, reward, term, trunc, info = env.step(action)
    result = info['action_result']
    print_result("File Listing", result)

def example_9_analyze_error():
    """Example 9: Analyze and fix Python errors"""
    print_section("Example 9: 🐍 Debug Python Error (Requires OPENAI_API_KEY)")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not configured. Skipping this example.")
        print("Configure it in .env to enable this feature.\n")
        return
    
    env = APEXEnv()
    env.reset()
    
    # Python error traceback
    error_text = """
Traceback (most recent call last):
  File "app.py", line 42, in process_data
    result = data['key']
KeyError: 'key'
    """
    
    action = DebugAction(
        error_text=error_text,
        language="python",
        action="analyze"
    )
    
    print("🐛 Analyzing Python error...\n")
    
    obs, reward, term, trunc, info = env.step(action)
    result = info['action_result']
    print_result("Error Analysis", result)

def example_10_multiple_searches():
    """Example 10: Batch multiple searches"""
    print_section("Example 10: 🔍 Batch Multiple Searches")
    
    env = APEXEnv()
    env.reset()
    
    queries = [
        "machine learning basics",
        "python best practices",
        "cloud computing trends"
    ]
    
    print(f"🔎 Performing {len(queries)} searches...\n")
    
    for i, query in enumerate(queries, 1):
        action = SearchAction(query=query, num_results=3)
        obs, reward, term, trunc, info = env.step(action)
        result = info['action_result']
        
        print(f"{i}. '{query}'")
        print(f"   Status: {'✅ Found' if result.success else '❌ Failed'}")
        if result.details and 'results' in result.details:
            print(f"   Results: {len(result.details['results'])} items")
        print()

def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("   APEX Advanced Features - Quick Start Examples")
    print("="*70)
    
    print("""
This script demonstrates 6 new features integrated into APEX:
  1. 🔍 Web Search (DuckDuckGo - no setup needed!)
  2. 🖼️  Image Search
  3. 📝 Summarize Text
  4. 🌐 Summarize Web Content  
  5. 💻 Generate Code
  6. 🔧 Fix Code
  7. ⚙️  Execute Commands
  8. 📁 List Files
  9. 🐍 Debug Errors
  10. 🔍 Batch Searches

Features with ⭐ require OPENAI_API_KEY in .env
Search examples work immediately with DuckDuckGo!

Starting examples...
    """)
    
    try:
        # Always runnable examples (no API keys needed)
        print("\n⭐ RUNNABLE IMMEDIATELY (No Setup):")
        example_1_web_search()
        example_10_multiple_searches()
        
        # Command execution examples
        print("\n▶️  COMMAND EXAMPLES (Local):")
        example_7_execute_command()
        example_8_list_files()
        
        # Examples requiring OpenAI
        print("\n🔑 REQUIRES OPENAI_API_KEY:")
        example_3_summarize_text()
        example_5_generate_code()
        example_6_fix_code()
        example_9_analyze_error()
        
        # Additional examples
        print("\n📋 ADDITIONAL EXAMPLES:")
        example_2_image_search()
        example_4_summarize_url()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    print_section("✅ Examples Complete!")
    print("""
Next Steps:
  1. Check verify_advanced_features.py for system status
  2. Read COMPREHENSIVE_ADVANCED_FEATURES_GUIDE.md for full documentation
  3. Start server: python run_server.py
  4. Visit: http://localhost:8000/docs
  5. Try your first action in the API!

Supported Features:
  ✅ Web Search (immediate, no setup)
  ✅ Image Search (immediate, no setup)
  ✅ Code Generation (with OPENAI_API_KEY)
  ✅ Code Fixing (with OPENAI_API_KEY)
  ✅ Content Summarization (with OPENAI_API_KEY)
  ✅ Command Execution (local, no setup)
  ✅ Error Analysis (with OPENAI_API_KEY)
  ✅ WhatsApp Integration (with WhatsApp Business API setup)

Happy coding! 🚀
    """)

if __name__ == "__main__":
    main()
