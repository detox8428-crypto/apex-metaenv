#!/usr/bin/env python
"""
APEX Advanced Features - Setup Verification Script

This script verifies that all 6 new features are properly installed and configured.
Run this to ensure everything is ready before using the advanced features.

Usage:
    python verify_advanced_features.py
"""

import os
import sys
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_file_exists(path, description):
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def check_import(module_name, description):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name}")
        print(f"   Error: {str(e)}")
        return False

def check_env_variable(var_name):
    """Check if an environment variable exists"""
    exists = os.getenv(var_name) is not None
    status = "✅" if exists else "⚠️"
    print(f"{status} {var_name}")
    return exists

def main():
    """Main verification function"""
    
    print_header("🔍 APEX Advanced Features - Setup Verification")
    
    print(f"Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # ====== MODULE FILES ======
    print_header("1️⃣  Checking Module Files")
    
    module_files = {
        "apex_env/whatsapp_integration.py": "WhatsApp Integration Module",
        "apex_env/search_provider.py": "Web Search Provider Module",
        "apex_env/content_summarizer.py": "Content Summarizer Module",
        "apex_env/code_generator.py": "Code Generator Module",
        "apex_env/command_executor.py": "Command Executor Module",
        "apex_env/vscode_debugger.py": "VS Code Debugger Module",
    }
    
    files_ok = 0
    for file_path, description in module_files.items():
        if check_file_exists(file_path, description):
            files_ok += 1
    
    print(f"\n✅ Module Files: {files_ok}/{len(module_files)} present")
    
    # ====== IMPORTS ======
    print_header("2️⃣  Checking Module Imports")
    
    modules = {
        "apex_env.whatsapp_integration": "WhatsApp Manager",
        "apex_env.search_provider": "Search Manager",
        "apex_env.content_summarizer": "Summarizer Manager",
        "apex_env.code_generator": "Code Generator Manager",
        "apex_env.command_executor": "Command Executor Manager",
        "apex_env.vscode_debugger": "VS Code Debugger Manager",
        "apex_env.models": "Action Models",
        "apex_env.environment": "APEX Environment",
    }
    
    imports_ok = 0
    for module_name, description in modules.items():
        if check_import(module_name, description):
            imports_ok += 1
    
    print(f"\n✅ Imports: {imports_ok}/{len(modules)} successful")
    
    # ====== ACTION TYPES ======
    print_header("3️⃣  Checking New Action Types")
    
    try:
        from apex_env.models import (
            WhatsAppAction, SearchAction, SummarizeAction,
            CodeGenAction, CommandExecAction, DebugAction
        )
        print("✅ WhatsAppAction")
        print("✅ SearchAction")
        print("✅ SummarizeAction")
        print("✅ CodeGenAction")
        print("✅ CommandExecAction")
        print("✅ DebugAction")
        print("\n✅ All 6 action types available")
        action_types_ok = True
    except ImportError as e:
        print(f"❌ Failed to import action types: {e}")
        action_types_ok = False
    
    # ====== ENVIRONMENT INTEGRATION ======
    print_header("4️⃣  Checking Environment Integration")
    
    try:
        from apex_env import APEXEnv
        from apex_env.models import SearchAction
        
        env = APEXEnv()
        obs = env.reset()
        print("✅ APEX Environment initializes")
        
        # Try a simple action
        action = SearchAction(query="test", num_results=1)
        obs, reward, term, trunc, info = env.step(action)
        print("✅ Environment can process actions")
        print("✅ Action dispatch working")
        
        env_integration_ok = True
    except Exception as e:
        print(f"❌ Environment integration error: {e}")
        env_integration_ok = False
    
    # ====== API KEY CONFIGURATION ======
    print_header("5️⃣  Checking API Key Configuration")
    
    print("Optional but Recommended:")
    
    api_keys = {
        "OPENAI_API_KEY": "OpenAI (Code Gen, Summarize, Debug)",
        "GOOGLE_API_KEY": "Google Search (Optional, DuckDuckGo works free)",
        "GOOGLE_SEARCH_ENGINE_ID": "Google Search Engine ID",
        "BING_SEARCH_KEY": "Bing Search (Optional)",
        "WHATSAPP_PHONE_NUMBER_ID": "WhatsApp Business Phone ID",
        "WHATSAPP_ACCESS_TOKEN": "WhatsApp Business Access Token",
    }
    
    configured_keys = 0
    for key_name, description in api_keys.items():
        if check_env_variable(key_name):
            configured_keys += 1
    
    print(f"\n✅ Configured: {configured_keys}/{len(api_keys)}")
    print(f"📝 Note: DuckDuckGo search works without any API key!")
    
    # ====== MANAGER STATUS ======
    print_header("6️⃣  Checking Manager Status")
    
    try:
        from apex_env.whatsapp_integration import whatsapp_manager
        from apex_env.search_provider import search_manager
        from apex_env.content_summarizer import summarizer_manager
        from apex_env.code_generator import code_generator_manager
        from apex_env.command_executor import command_executor_manager
        from apex_env.vscode_debugger import vscode_debugger_manager
        
        managers = [
            ("WhatsApp", whatsapp_manager),
            ("Search", search_manager),
            ("Summarizer", summarizer_manager),
            ("CodeGen", code_generator_manager),
            ("CmdExec", command_executor_manager),
            ("Debugger", vscode_debugger_manager),
        ]
        
        for name, manager in managers:
            try:
                status = manager.get_status()
                enabled = status.get("enabled", True)
                emoji = "✅" if enabled else "⚠️"
                print(f"{emoji} {name}: {'Enabled' if enabled else 'Needs Configuration'}")
            except Exception as e:
                print(f"❌ {name}: Error checking status - {str(e)}")
        
        print("\n✅ All managers instantiated successfully")
        managers_ok = True
    except Exception as e:
        print(f"❌ Manager initialization error: {e}")
        managers_ok = False
    
    # ====== DOCUMENTATION ======
    print_header("7️⃣  Checking Documentation")
    
    docs = {
        "COMPREHENSIVE_ADVANCED_FEATURES_GUIDE.md": "Comprehensive Guide (50+ pages)",
        "ADVANCED_FEATURES_QUICK_REFERENCE.md": "Quick Reference",
        "APEX_ADVANCED_FEATURES_BUILD_SUMMARY.md": "Build Summary",
    }
    
    docs_ok = 0
    for file_path, description in docs.items():
        if check_file_exists(file_path, description):
            docs_ok += 1
    
    print(f"\n✅ Documentation: {docs_ok}/{len(docs)} files present")
    
    # ====== SUMMARY ======
    print_header("📊 Verification Summary")
    
    all_checks = [
        ("Module Files", files_ok == len(module_files)),
        ("Imports", imports_ok == len(modules)),
        ("Action Types", action_types_ok),
        ("Environment Integration", env_integration_ok),
        ("Manager Status", managers_ok),
        ("Documentation", docs_ok == len(docs)),
    ]
    
    passed = sum(1 for _, result in all_checks if result)
    total = len(all_checks)
    
    for check_name, result in all_checks:
        emoji = "✅" if result else "⚠️"
        print(f"{emoji} {check_name}")
    
    print(f"\n{'='*60}")
    print(f"  Overall Status: {passed}/{total} checks passed")
    print(f"{'='*60}\n")
    
    # ====== RECOMMENDATIONS ======
    print_header("🎯 Recommendations")
    
    if configured_keys < 2:
        print("1. ⭐ Add OPENAI_API_KEY to .env for:")
        print("   - Code generation & fixing")
        print("   - Content summarization")
        print("   - Error analysis & debugging")
    
    if not os.path.exists(".env"):
        print("2. ⭐ Create .env file with configuration")
    
    print("3. 🚀 Start the server: python run_server.py")
    print("4. 🌐 Visit API docs: http://localhost:8000/docs")
    print("5. 🧪 Try a search action (no setup needed!)")
    
    # ====== QUICK START ======
    print_header("⚡ Quick Start")
    
    print("""
from apex_env import APEXEnv
from apex_env.models import SearchAction

# Initialize environment
env = APEXEnv()
obs = env.reset()

# Try a search (works immediately!)
action = SearchAction(query="python tutorials", num_results=5)
obs, reward, term, trunc, info = env.step(action)

print(f"Reward: {reward.total_reward:.3f}")
print(f"Search results: {info['action_result'].details}")
    """)
    
    # ====== FINAL STATUS ======
    if passed == total:
        print_header("✨ All Systems Go! ✨")
        print("You're ready to use advanced features!")
        print("\n🎉 APEX Advanced Features are fully operational!")
        print("\nStart with:")
        print("  1. python run_server.py")
        print("  2. Visit http://localhost:8000/docs")
        print("  3. Try a SearchAction")
        return 0
    else:
        print_header("⚠️  Some Issues Found")
        print("Not all systems are ready. Please:")
        print("  1. Check the errors above")
        print("  2. Verify all files exist")
        print("  3. Check module imports")
        print("  4. Review .env configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
