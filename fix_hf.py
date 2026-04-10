#!/usr/bin/env python3
"""Fix pyproject.toml on HuggingFace Space"""

from huggingface_hub import hf_hub_download, CommitScheduler
import os
from pathlib import Path

# HF credentials from environment
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable is required")
SPACE_REPO = "ShaikB/Apex"

print("📥 Downloading pyproject.toml from HF...")
try:
    # Download current file
    file_path = hf_hub_download(
        repo_id=SPACE_REPO,
        repo_type="space",
        filename="pyproject.toml",
        token=HF_TOKEN,
    )
    
    # Read content
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("✅ Downloaded successfully")
    print("\n📝 Current [project.scripts] section:")
    for line in content.split('\n'):
        if 'server' in line or 'apex' in line:
            print(f"   {line}")
    
    # Replace the entry point
    print("\n🔧 Fixing entry point...")
    new_content = content.replace('server = "app:app"', 'server = "app:main"')
    
    # Remove the old apex-code-solver line if present
    lines = new_content.split('\n')
    lines = [line for line in lines if 'apex-code-solver' not in line]
    new_content = '\n'.join(lines)
    
    # Write back locally
    with open("pyproject.toml", 'w') as f:
        f.write(new_content)
    
    # Upload using CommitScheduler (reliable for HF)
    print("📤 Uploading to HF...")
    scheduler = CommitScheduler(
        repo_id=SPACE_REPO,
        repo_type="space",
        token=HF_TOKEN,
        folder_path=".",
    )
    scheduler.schedule_upload("pyproject.toml", "pyproject.toml")
    scheduler.wait_and_commit("fix: server entry point callable for openenv validate")
    
    print("\n✅ Successfully fixed and uploaded to HF!")
    print("⏳ Wait 60 seconds for Space rebuild...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
