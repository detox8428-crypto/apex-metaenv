#!/usr/bin/env python3
"""
Simple Test Script for APEX API
Tests local environment directly (not HTTP)
"""

import asyncio
import logging
from envs.code_solver_env.server.code_solver_environment import CodeSolverEnvironment

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def test_local_api():
    """Test local environment directly"""
    
    # Create SINGLE global environment instance
    env = CodeSolverEnvironment()
    
    logger.info("=" * 80)
    logger.info("APEX ENGINEERING BENCHMARK - API Test")
    logger.info("=" * 80)
    
    domains = ["data_pipeline", "code_review", "incident_debug"]
    difficulties = ["easy", "medium", "hard"]
    
    results = []
    
    for domain in domains:
        for difficulty in difficulties:
            task_type = "solve" if domain == "data_pipeline" else "review" if domain == "code_review" else "debug"
            
            logger.info(f"\n[TEST] {domain} / {task_type} / {difficulty}")
            
            try:
                # Reset - use single env instance
                session_id, observation = await env.reset(
                    domain=domain,
                    difficulty=difficulty,
                    mode=task_type
                )
                
                logger.info(f"  ✅ Reset: session_id={session_id}")
                logger.info(f"  📋 Task: {observation.task_id}")
                
                # Step - use same env instance
                if task_type == "solve":
                    code = "import pandas as pd\ndef process(df):\n    return df"
                    result = await env.step(session_id=session_id, code=code)
                elif task_type == "review":
                    review = {
                        "problem_identified": "N+1 query",
                        "production_impact": "timeout at scale",
                        "fix_approach": "batch query",
                        "fixed_code": "def get(ids):\n    return db.query().filter(id.in_(ids))"
                    }
                    result = await env.step(session_id=session_id, review=review)
                else:  # debug
                    code = "# Fix missing null check\nif not user:\n    raise ValueError()"
                    result = await env.step(session_id=session_id, code=code)
                
                # Parse result
                if isinstance(result, tuple) and len(result) >= 5:
                    obs, reward, terminated, truncated, info = result
                else:
                    raise ValueError(f"Unexpected result format: {result}")
                
                logger.info(f"  ✅ Step: reward={reward:.3f}, done={terminated or truncated}")
                results.append({
                    "domain": domain,
                    "task_type": task_type,
                    "difficulty": difficulty,
                    "success": True,
                    "reward": reward
                })
                
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
                results.append({
                    "domain": domain,
                    "task_type": task_type,
                    "difficulty": difficulty,
                    "success": False,
                    "reward": 0.0
                })
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    
    total = len(results)
    success = sum(1 for r in results if r["success"])
    avg_reward = sum(r["reward"] for r in results) / total if total > 0 else 0
    
    logger.info(f"Episodes: {success}/{total} successful")
    logger.info(f"Average reward: {avg_reward:.3f}")
    
    by_domain = {}
    for r in results:
        domain = r["domain"]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(r["reward"])
    
    for domain, rewards in by_domain.items():
        avg = sum(rewards) / len(rewards) if rewards else 0
        logger.info(f"  {domain}: {avg:.3f}")


async def main():
    await test_local_api()


if __name__ == "__main__":
    asyncio.run(main())
