#!/usr/bin/env python3
"""
OpenEnv Inference - Email Triage Agent

This script runs an LLM-based agent that triages emails.
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
from typing import Optional

# Get environment variables (injected by dashboard)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
MAX_STEPS = 5

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import environment classes
sys.path.insert(0, os.path.dirname(__file__))
from envs.email_triage_env import EmailTriageEnv, EmailTriageAction

# Try to import OpenAI, fallback to requests if not available
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    import requests as openai_requests


def call_llm(prompt: str, max_tokens: int = 200) -> str:
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
                timeout=10
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"LLM request failed: {e}, using fallback response")
            return '{"priority": "normal", "category": "support", "action": "reply"}'
    
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
        logger.warning(f"LLM call failed: {e}, using fallback response")
        return '{"priority": "normal", "category": "support", "action": "reply"}'


def extract_json_from_response(text: str) -> Optional[dict]:
    """Extract JSON from LLM response"""
    try:
        # Try direct JSON parsing
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in text
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    
    return None


def run_episode(task_name: str, max_steps: int = 5) -> dict:
    """
    Run a single episode of email triage
    
    Args:
        task_name: Name of the task (e.g., "easy_triage", "medium_triage", "hard_triage")
        max_steps: Maximum steps per episode
        
    Returns:
        Dictionary with episode statistics
    """
    rewards = []
    
    try:
        with EmailTriageEnv(base_url=ENV_URL).sync() as env:
            # Reset environment
            obs = env.reset()
            
            # [START] marker
            print(f"[START] task={task_name} env=email-triage-env model={MODEL_NAME}")
            
            for step in range(1, max_steps + 1):
                # Build prompt for LLM
                prompt = f"""You are an expert email triage agent. Analyze the email and make three decisions:
1. Priority: urgent, high, normal, or low
2. Category: bug, feature, billing, support, or spam
3. Action: reply, escalate, archive, delete, or forward

Email Subject: {obs.subject}
Email Body: {obs.body}
From: {obs.sender}

Respond with ONLY a JSON object (no other text):
{{"priority": "...", "category": "...", "action": "...", "reasoning": "..."}}"""
                
                # Call LLM
                raw_response = call_llm(prompt)
                
                # Parse response
                parsed = extract_json_from_response(raw_response)
                
                if parsed is None:
                    # Fallback to defaults
                    action = EmailTriageAction(
                        priority="normal",
                        category="support",
                        action="reply",
                        reasoning="LLM response parsing failed"
                    )
                else:
                    action = EmailTriageAction(
                        priority=parsed.get("priority", "normal"),
                        category=parsed.get("category", "support"),
                        action=parsed.get("action", "reply"),
                        reasoning=parsed.get("reasoning", "")
                    )
                
                # Execute step
                obs, reward, done = env.step(action)
                rewards.append(reward)
                
                # [STEP] marker
                action_str = f"priority={action.priority},category={action.category},action={action.action}"
                feedback = obs.feedback or "null"
                print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={str(done).lower()} error={json.dumps(feedback)}")
                
                if done:
                    break
            
            # Determine success (at least one step with reward >= 0.8)
            success = any(r >= 0.8 for r in rewards)
            rewards_str = ",".join(f"{r:.2f}" for r in rewards)
            
            # [END] marker
            print(f"[END] success={str(success).lower()} steps={len(rewards)} rewards={rewards_str}")
            
            return {
                "task": task_name,
                "success": success,
                "steps": len(rewards),
                "rewards": rewards,
                "avg_reward": sum(rewards) / len(rewards) if rewards else 0.0
            }
            
    except Exception as e:
        logger.error(f"Episode failed: {e}")
        print(f"[END] success=false steps=0 rewards=")
        return {
            "task": task_name,
            "success": False,
            "steps": 0,
            "rewards": [],
            "error": str(e)
        }


def main():
    """Main entry point - run agent on environment"""
    logger.info(f"OpenEnv Inference - Email Triage")
    logger.info(f"Environment URL: {ENV_URL}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"API Base: {API_BASE_URL}")
    
    all_results = []
    
    # Run 3 different tasks (easy, medium, hard)
    tasks = ["easy_triage", "medium_triage", "hard_triage"]
    
    for task_name in tasks:
        result = run_episode(task_name, max_steps=MAX_STEPS)
        all_results.append(result)
    
    # Summary
    total_success = sum(1 for r in all_results if r["success"])
    avg_reward = sum(r.get("avg_reward", 0.0) for r in all_results) / len(all_results)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Summary:")
    logger.info(f"  Tasks completed: {len(all_results)}")
    logger.info(f"  Successful: {total_success}/{len(all_results)}")
    logger.info(f"  Average reward: {avg_reward:.2f}")
    logger.info(f"{'='*60}")
    
    # Exit with success code if at least one task succeeded
    sys.exit(0 if total_success > 0 else 1)


if __name__ == "__main__":
    main()
