#!/usr/bin/env python3
"""
APEX Production Validation and Startup Script

Validates all components and starts the server if everything is working.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_python_version():
    """Verify Python version."""
    print("✓ Checking Python version...")
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        print(f"  ❌ Python 3.8+ required (found {version_info.major}.{version_info.minor})")
        return False
    print(f"  ✓ Python {version_info.major}.{version_info.minor}.{version_info.micro}")
    return True


def check_dependencies():
    """Verify all dependencies are installed."""
    print("✓ Checking dependencies...")
    required = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('requests', 'Requests'),
        ('yaml', 'PyYAML'),
        ('dateutil', 'python-dateutil'),
    ]
    
    optional = [
        ('openai', 'OpenAI'),
        ('dotenv', 'python-dotenv'),
    ]
    
    all_good = True
    
    # Check required
    for module, name in required:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ❌ {name} - Install with: pip install {name.lower().replace(' ', '-')}")
            all_good = False
    
    # Check optional
    for module, name in optional:
        try:
            __import__(module)
            print(f"  ✓ {name} (optional)")
        except ImportError:
            print(f"  ⚠  {name} (optional) - Install with: pip install {name.lower().replace(' ', '-')}")
    
    return all_good


def check_config():
    """Verify configuration files exist."""
    print("✓ Checking configuration files...")
    
    config_file = project_root / "openenv.yaml"
    if config_file.exists():
        print(f"  ✓ openenv.yaml found ({config_file.stat().st_size} bytes)")
        try:
            from config import ConfigLoader
            config = ConfigLoader.load_config(str(config_file))
            print(f"  ✓ Configuration loaded successfully")
            return True
        except Exception as e:
            print(f"  ❌ Failed to load config: {e}")
            return False
    else:
        print(f"  ❌ openenv.yaml not found at {config_file}")
        return False


def check_modules():
    """Verify all Python modules can be imported."""
    print("✓ Checking Python modules...")
    
    modules = [
        ('apex_env', 'APEX Environment'),
        ('server', 'FastAPI Server'),
        ('inference', 'Inference Module'),
        ('config', 'Config Loader'),
        ('client_example', 'Python Client'),
    ]
    
    all_good = True
    for module, name in modules:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
            all_good = False
    
    return all_good


def check_apex_env():
    """Verify APEX Environment package."""
    print("✓ Checking APEX Environment package...")
    
    try:
        from apex_env import APEXEnv, EnvironmentConfig
        
        # Try to create an environment
        config = EnvironmentConfig(max_episode_steps=10, seed=42)
        env = APEXEnv(config=config)
        obs = env.reset()
        
        print(f"  ✓ Environment created successfully")
        
        # Try a simple action
        from apex_env import EmailAction, LanguageEnum, PriorityEnum
        action = EmailAction(
            recipient_id=0,
            subject="Test",
            body="Test body",
            priority=PriorityEnum.MEDIUM,
            language=LanguageEnum.EN,
        )
        
        obs, reward, done, truncated, info = env.step(action)
        print(f"  ✓ Step executed: reward={reward}")
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_inference():
    """Verify inference module."""
    print("✓ Checking inference module...")
    
    try:
        from inference import APEXInferenceClient
        client = APEXInferenceClient()
        print(f"  ✓ Inference client initialized")
        print(f"    - API Base URL: {client.api_base_url}")
        print(f"    - Model: {client.model_name}")
        return True
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def validate_imports():
    """Validate all critical imports work."""
    print("✓ Validating critical imports...")
    
    try:
        from apex_env import (
            APEXEnv, EnvironmentConfig,
            EmailAction, MeetingAction, TranslationAction, GestureAction, NoOpAction,
            LanguageEnum, PriorityEnum, MeetingTypeEnum, GestureEnum,
        )
        print("  ✓ All APEX imports successful")
        
        from server import app
        print("  ✓ FastAPI app imports successful")
        
        from inference import APEXInferenceClient
        print("  ✓ Inference imports successful")
        
        from config import ConfigLoader
        print("  ✓ Config loader imports successful")
        
        return True
    
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False


def main():
    """Run all validations."""
    print("=" * 70)
    print("APEX ENVIRONMENT - PRODUCTION VALIDATION")
    print("=" * 70)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Import Validation", validate_imports),
        ("Python Modules", check_modules),
        ("APEX Environment", check_apex_env),
        ("Inference Module", check_inference),
    ]
    
    results = []
    for name, check_func in checks:
        print()
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {name}")
    
    print()
    print(f"Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("=" * 70)
        print("✅ ALL VALIDATIONS PASSED - READY FOR PRODUCTION")
        print("=" * 70)
        print()
        print("To start the server, run:")
        print("  python run_server.py")
        print()
        print("API Documentation will be available at:")
        print("  http://localhost:8000/docs")
        print()
        return 0
    else:
        print()
        print("=" * 70)
        print("❌ SOME VALIDATIONS FAILED - FIX ISSUES BEFORE PRODUCTION")
        print("=" * 70)
        print()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
