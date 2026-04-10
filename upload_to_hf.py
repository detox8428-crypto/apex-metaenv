#!/usr/bin/env python3
"""Upload app.py directly to HuggingFace Space"""

from huggingface_hub import upload_file
import os
from pathlib import Path

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable is required")
SPACE_REPO = "ShaikB/Apex"
LOCAL_FILE = "app.py"

print("📤 Uploading app.py to HuggingFace Space...")
print(f"   Repo: {SPACE_REPO}")
print(f"   File: {LOCAL_FILE}")

try:
    # Upload the file
    url = upload_file(
        path_or_fileobj=LOCAL_FILE,
        path_in_repo=LOCAL_FILE,
        repo_id=SPACE_REPO,
        repo_type="space",
        token=HF_TOKEN,
        commit_message="fix: add main() function for openenv validate"
    )
    
    print(f"✅ Successfully uploaded!")
    print(f"   URL: {url}")
    print(f"\n⏳ HuggingFace Space will rebuild in 30-60 seconds...")
    print(f"   Check: https://huggingface.co/spaces/{SPACE_REPO}")
    
except Exception as e:
    print(f"❌ Upload failed: {e}")
    import traceback
    traceback.print_exc()
