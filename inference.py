#!/usr/bin/env python3
"""
OpenEnv Inference - Code Solver Agent

This script runs an LLM-based agent that solves coding problems.
Used by hackathon dashboard for agent evaluation.

Output format:
- [START] task=... env=... model=...
- [STEP] step=... action=... reward=... done=... error=...
- [END] success=... steps=... rewards=...
"""

import os
import sys
import json
import logging
import re
from typing import Optional

# Get environment variables (injected by dashboard)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
MAX_STEPS = 3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import environment classes
sys.path.insert(0, os.path.dirname(__file__))
from envs.code_solver_env import CodeSolverEnv, CodeSolverAction

# Try to import OpenAI, fallback to requests if not available
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    import requests as openai_requests


def call_llm(prompt: str, max_tokens: int = 1000) -> str:
    """Call LLM with prompt and return response"""
    if not HAS_OPENAI:
        # Fallback: use requests directly
        try:
            response = openai_requests.post(
                f"{API_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.1
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"LLM request failed: {e}, using simple solution")
            return "def solution():\n    pass"
    
    try:
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"LLM call failed: {e}, using simple solution")
        return "def solution():\n    pass"


def extract_code_from_response(text: str) -> str:
    """Extract Python code from LLM response"""
    # Try to find code block with python marker
    match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    
    # Try to find any code block
    match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    
    # If no code block, return the whole response (might be raw code)
    return text.strip()


def run_episode(difficulty: str) -> dict:
    """
    Run a single episode of code solving
    
    Args:
        difficulty: Problem difficulty (easy, medium, hard)
        
    Returns:
        Dictionary with episode statistics
    """
    rewards = []
    task_name = f"{difficulty}-solver"
    
    try:
        env = CodeSolverEnv(base_url=ENV_URL)
        
        # Reset environment with specific difficulty
        obs = env.reset(difficulty=difficulty)
        
        # [START] marker
        print(f"[START] task={task_name} env=code-solver-env model={MODEL_NAME}")
        
        for step in range(1, MAX_STEPS + 1):
            # Build prompt for LLM
            prompt = f"""You are a coding expert. Solve this programming problem:

Problem: {obs.title}
Difficulty: {obs.difficulty}

Description:
{obs.description}

Function Signature:
{obs.function_signature}

Examples:
{obs.examples}

Constraints:
{obs.constraints}

Write ONLY the complete Python function that solves this problem. 
Do NOT include any explanations, test code, or anything else.
Start directly with the function definition.

If you provide code in a code block (```python ... ```), only the code inside will be used."""
            
            # Call LLM
            raw_response = call_llm(prompt)
            
            # Extract code from response
            code = extract_code_from_response(raw_response)
            
            # Execute step
            obs, reward, done = env.step(CodeSolverAction(code=code))
            rewards.append(reward)
            
            # Format action string (shortened for output)
            action_summary = f"write_code({obs.passed_cases}/{obs.total_cases}_tests)"
            
            # [STEP] marker
            error_msg = obs.error_message if obs.error_message else "null"
            print(f"[STEP] step={step} action={action_summary} reward={reward:.2f} done={str(done).lower()} error={json.dumps(error_msg)}")
            
            if done:
                break
        
        # Determine success (reward >= 0.8 means at least 80% tests pass)
        success = any(r >= 0.8 for r in rewards)
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        
        # [END] marker
        print(f"[END] success={str(success).lower()} steps={len(rewards)} rewards={rewards_str}")
        
        return {
            "task": task_name,
            "difficulty": difficulty,
            "success": success,
            "steps": len(rewards),
            "rewards": rewards,
            "avg_reward": sum(rewards) / len(rewards) if rewards else 0.0
        }
        
    except Exception as e:
        logger.error(f"Episode {task_name} failed: {e}", exc_info=True)
        print(f"[END] success=false steps=0 rewards=")
        return {
            "task": task_name,
            "difficulty": difficulty,
            "success": False,
            "steps": 0,
            "rewards": [],
            "error": str(e)
        }


def main():
    """Main entry point - run agent on environment"""
    logger.info(f"OpenEnv Inference - Code Solver")
    logger.info(f"Environment URL: {ENV_URL}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"API Base: {API_BASE_URL}")
    
    all_results = []
    
    # Run 3 episodes with different difficulties
    difficulties = ["easy", "medium", "hard"]
    
    for difficulty in difficulties:
        result = run_episode(difficulty)
        all_results.append(result)
    
    # Summary
    total_success = sum(1 for r in all_results if r["success"])
    avg_reward = sum(r.get("avg_reward", 0.0) for r in all_results) / len(all_results)
    total_steps = sum(r.get("steps", 0) for r in all_results)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Summary:")
    logger.info(f"  Episodes: {len(all_results)}")
    logger.info(f"  Successful: {total_success}/{len(all_results)}")
    logger.info(f"  Total steps: {total_steps}")
    logger.info(f"  Average reward: {avg_reward:.2f}")
    logger.info(f"{'='*60}")
    
    # Exit with success code if at least one episode succeeded
    sys.exit(0 if total_success > 0 else 1)


if __name__ == "__main__":
    main()
