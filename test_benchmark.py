#!/usr/bin/env python3
"""
APEX Quick Inference Test
Runs 9 episodes and prints results
"""

import sys
import logging
from environment import APEXEnvironment

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def generate_response(domain: str, task_id: str):
    """Generate appropriate response for domain"""
    if domain == "data_pipeline":
        return """import pandas as pd
def aggregate_sales(df):
    return df.groupby('customer_id')['amount'].sum().sort_values(ascending=False).to_dict()
"""
    elif domain == "code_review":
        return """The code has a critical N+1 query problem. 

BUG: The loop queries the database once per user. With 10,000 users, this means 10,000 database queries instead of 1-2!

PRODUCTION IMPACT:
- Each query takes 10-100ms, so total time = 100-1000 seconds
- Service times out at 30 seconds
- All affected users see "Connection timeout"
- At scale with millions of users, this completely breaks the API

FIX:
- Use prefetch_related() to fetch all orders in ONE batch query
- Or use select_related() + annotate(Count()) to avoid separate queries
- Replace the loop with bulk ORM operations
"""
    else:  # incident_debug
        return """ROOT CAUSE ANALYSIS:

Step 1: The auth service is timing out because the database connection pool is exhausted.
- 10 database connections all in use
- New requests wait for a connection
- After 30 seconds, they timeout

Step 2: Timeouts cause client retry logic to activate.
- Clients retry immediately without backoff
- This creates a retry storm: 1000+ retry requests/second
- Further exhausts the database

Step 3: Circuit breaker is stuck in a bad state.
- Too many failures cause circuit to open
- But it's not resetting correctly
- Service fails even when database recovers

FIX:
1. Increase connection pool from 10 to 100
2. Add exponential backoff to retry logic (1s, 2s, 4s...)
3. Implement circuit breaker reset mechanism
4. Add graceful degradation (serve stale cache data)
"""


def main():
    print("=" * 80)
    print("APEX ENGINEERING BENCHMARK v3.0")
    print("9 Episodes across 3 domains")
    print("=" * 80)
    print()
    
    env = APEXEnvironment()
    episodes = [
        ("data_pipeline", "easy"),
        ("data_pipeline", "medium"),
        ("data_pipeline", "hard"),
        ("code_review", "easy"),
        ("code_review", "medium"),
        ("code_review", "hard"),
        ("incident_debug", "easy"),
        ("incident_debug", "medium"),
        ("incident_debug", "hard"),
    ]
    
    all_scores = []
    domain_scores = {}
    
    for domain, difficulty in episodes:
        # Reset
        session_id, obs = env.reset(domain=domain, difficulty=difficulty)
        task_id = obs.task_id
        
        print(f"[START] task={task_id} domain={domain}")
        
        rewards = []
        
        for step in range(1, obs.max_steps + 1):
            # Generate response
            response = generate_response(domain, task_id)
            
            # Submit step
            if domain == "data_pipeline":
                obs_out, reward, done, info = env.step(session_id=session_id, code=response)
            elif domain == "code_review":
                obs_out, reward, done, info = env.step(session_id=session_id, review=response)
            else:
                obs_out, reward, done, info = env.step(session_id=session_id, diagnosis=response)
            
            rewards.append(reward)
            passed = info.get("passed_cases", "N/A")
            total = info.get("total_cases", "N/A")
            feedback = info.get("feedback", "")[:40]
            
            print(f"[STEP {step}] reward={reward:.2f} passed_cases={passed}/{total} info={feedback}")
            
            if done:
                break
        
        final_score = max(rewards) if rewards else 0.0
        success = final_score >= 0.5
        all_scores.append(final_score)
        domain_scores.setdefault(domain, []).append(final_score)
        
        print(f"[END] success={str(success).lower()} steps={len(rewards)} score={final_score:.2f} rewards={[round(r, 2) for r in rewards]}")
        print()
    
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Episodes completed: {len(all_scores)}/9")
    if all_scores:
        print(f"Average reward: {sum(all_scores)/len(all_scores):.4f}")
    print()
    print("Per-Domain Performance:")
    for domain in ["data_pipeline", "code_review", "incident_debug"]:
        scores = domain_scores.get(domain, [])
        if scores:
            avg = sum(scores) / len(scores)
            print(f"  {domain:<20} → avg={avg:.4f} ({len(scores)} episodes)")
    print("=" * 80)


if __name__ == "__main__":
    main()
