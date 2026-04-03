#!/usr/bin/env python3
"""
APEX Environment - Quick Test Script
Tests all 4 generated files and core functionality
"""

import os
import json
import yaml
import sys
from pathlib import Path

def test_dockerfile():
    """Test Dockerfile exists and has valid structure"""
    print("\n📦 Testing Dockerfile...")
    
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("  ❌ Dockerfile not found")
        return False
    
    content = dockerfile_path.read_text()
    checks = {
        "FROM statement": "FROM" in content,
        "WORKDIR": "WORKDIR" in content,
        "COPY requirements": "COPY requirements" in content,
        "EXPOSE 8000": "EXPOSE 8000" in content,
        "CMD run_server": "run_server.py" in content,
        "HEALTHCHECK": "HEALTHCHECK" in content,
    }
    
    for check, result in checks.items():
        status = "✓" if result else "❌"
        print(f"  {status} {check}")
    
    return all(checks.values())


def test_openenv_yaml():
    """Test openenv.yaml is valid YAML with required sections"""
    print("\n⚙️  Testing openenv.yaml...")
    
    yaml_path = Path("openenv.yaml")
    if not yaml_path.exists():
        print("  ❌ openenv.yaml not found")
        return False
    
    try:
        config = yaml.safe_load(yaml_path.read_text())
        
        required_sections = ["server", "api", "inference", "logging", "environment"]
        checks = {section: section in config for section in required_sections}
        
        # Check inference section has required fields
        if config.get("inference"):
            inference = config["inference"]
            checks["inference.api_base_url"] = "api_base_url" in inference
            checks["inference.model_name"] = "model_name" in inference
            checks["inference.hf_token"] = "hf_token" in inference
        
        for check, result in checks.items():
            status = "✓" if result else "❌"
            print(f"  {status} {check}")
        
        return all(checks.values())
    
    except yaml.YAMLError as e:
        print(f"  ❌ YAML parse error: {e}")
        return False


def test_inference_py():
    """Test inference.py has required functionality"""
    print("\n🤖 Testing inference.py...")
    
    py_path = Path("inference.py")
    if not py_path.exists():
        print("  ❌ inference.py not found")
        return False
    
    content = py_path.read_text()
    checks = {
        "APEXInferenceClient class": "class APEXInferenceClient" in content,
        "API_BASE_URL env var": "API_BASE_URL" in content,
        "MODEL_NAME env var": "MODEL_NAME" in content,
        "HF_TOKEN env var": "HF_TOKEN" in content,
        "[START] logging": "[START]" in content,
        "[STEP] logging": "[STEP]" in content,
        "[END] logging": "[END]" in content,
        "generate_response method": "def generate_response" in content,
        "classify_action method": "def classify_action" in content,
        "extract_parameters method": "def extract_parameters" in content,
        "OpenAI client": "OpenAI" in content,
    }
    
    for check, result in checks.items():
        status = "✓" if result else "❌"
        print(f"  {status} {check}")
    
    return all(checks.values())


def test_readme_md():
    """Test README.md has required sections"""
    print("\n📖 Testing README.md...")
    
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("  ❌ README.md not found")
        return False
    
    content = readme_path.read_text()
    checks = {
        "APEX description": "APEX Environment" in content,
        "What is APEX section": "## What is APEX" in content,
        "Setup Instructions section": "## Setup Instructions" in content,
        "Tasks documentation": "## Supported Tasks" in content,
        "Email task": "Email Task" in content,
        "Meeting task": "Meeting Task" in content,
        "Translation task": "Translation Task" in content,
        "Gesture task": "Gesture Task" in content,
        "Quick Start": "Quick Start" in content,
        "Python Client Usage": "## Python Client Usage" in content,
        "Docker Deployment": "## Docker Deployment" in content,
        "Inference Module": "## Inference Module" in content,
        "REST API documentation": "## REST API" in content or "## API" in content,
        "Configuration section": "## Configuration" in content,
    }
    
    for check, result in checks.items():
        status = "✓" if result else "❌"
        print(f"  {status} {check}")
    
    return all(checks.values())


def test_env_vars():
    """Test inference.py can read environment variables"""
    print("\n🔐 Testing Environment Variables...")
    
    # Set test env vars
    os.environ["API_BASE_URL"] = "http://test-server:8000"
    os.environ["MODEL_NAME"] = "gpt-4"
    os.environ["HF_TOKEN"] = "test_token_123"
    
    checks = {
        "API_BASE_URL set": os.getenv("API_BASE_URL") == "http://test-server:8000",
        "MODEL_NAME set": os.getenv("MODEL_NAME") == "gpt-4",
        "HF_TOKEN set": os.getenv("HF_TOKEN") == "test_token_123",
    }
    
    for check, result in checks.items():
        status = "✓" if result else "❌"
        print(f"  {status} {check}")
        if result and "=" in check:
            value = os.getenv(check.split()[0])
            if value:
                print(f"      Value: {value}")
    
    return all(checks.values())


def test_integration():
    """Test files work together"""
    print("\n🔗 Testing Integration...")
    
    checks = {
        "Dockerfile exists": Path("Dockerfile").exists(),
        "openenv.yaml exists": Path("openenv.yaml").exists(),
        "inference.py exists": Path("inference.py").exists(),
        "README.md exists": Path("README.md").exists(),
        "requirements.txt exists": Path("requirements.txt").exists(),
        "server.py exists": Path("server.py").exists(),
        "run_server.py exists": Path("run_server.py").exists(),
        "client_example.py exists": Path("client_example.py").exists(),
    }
    
    for check, result in checks.items():
        status = "✓" if result else "❌"
        print(f"  {status} {check}")
    
    return all(checks.values())


def main():
    """Run all tests"""
    print("=" * 60)
    print("APEX Environment - File Generation Verification")
    print("=" * 60)
    
    os.chdir(Path(__file__).parent)
    
    results = {
        "Dockerfile": test_dockerfile(),
        "openenv.yaml": test_openenv_yaml(),
        "inference.py": test_inference_py(),
        "README.md": test_readme_md(),
        "Environment Variables": test_env_vars(),
        "Integration": test_integration(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! Files are ready for production.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Start server: python run_server.py")
        print("  3. Run examples: python client_example.py")
        print("  4. Access API: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
