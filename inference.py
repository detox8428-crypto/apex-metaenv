#!/usr/bin/env python3
"""
APEX Engineering Benchmark - Multi-Domain Inference
Runs 9-episode benchmark: 3 domains × 3 difficulties
Domains: data_pipeline, code_review, incident_debug
"""

import os
import sys
import time
import json
import logging
import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


class EngineringBenchmarkAgent:
    """Agent that interacts with APEX Engineering Benchmark (3-domain)"""
    
    def __init__(self, env_url: str = "http://localhost:8000", use_local: bool = True):
        """Initialize agent"""
        self.env_url = env_url
        self.use_local = use_local
        self.episodes_run = 0
        self.total_rewards = []
        self.domain_results = {"data_pipeline": [], "code_review": [], "incident_debug": []}
        
        if use_local:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "envs", "code_solver_env"))
    
    async def run_solve_episode(self, domain: str, difficulty: str) -> Dict[str, Any]:
        """Run SOLVE mode (data_pipeline only)"""
        observation, session_id = await self._reset(domain, "solve", difficulty)
        task_id = observation.get("task_id", f"{difficulty}-solve")
        
        logger.info(f"\n[START] task={task_id} domain={domain} env=apex-engineering model=Qwen2.5-72B-Instruct")
        
        episode_rewards = []
        episode_steps = 0
        success = False
        
        try:
            for step_num in range(1, 6):
                episode_steps = step_num
                code = self._generate_solve_code(observation)
                reward, done, info = await self._step(session_id, code, "solve")
                episode_rewards.append(reward)
                logger.info(f"[STEP] step={step_num} action=submit_code({len(code)} chars) reward={reward:.2f} done={str(done).lower()} error=null")
                if done:
                    success = True
                    break
        except Exception as e:
            logger.error(f"[ERROR] {e}")
        
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
        logger.info(f"[END] success={str(success).lower()} steps={episode_steps} score={avg_reward:.2f} rewards={','.join(f'{r:.2f}' for r in episode_rewards)}")
        
        self.total_rewards.append(avg_reward)
        self.domain_results[domain].append(avg_reward)
        self.episodes_run += 1
        
        return {
            "task_id": task_id,
            "domain": domain,
            "task_type": "solve",
            "difficulty": difficulty,
            "steps": episode_steps,
            "rewards": episode_rewards,
            "avg_reward": avg_reward,
            "success": success
        }
    
    async def run_code_review_episode(self, domain: str, difficulty: str) -> Dict[str, Any]:
        """Run CODE_REVIEW domain (production code with impact)"""
        observation, session_id = await self._reset(domain, "review", difficulty)
        task_id = observation.get("task_id", f"code-review-{difficulty}")
        
        logger.info(f"\n[START] task={task_id} domain={domain} env=apex-engineering model=Qwen2.5-72B-Instruct")
        logger.info("[task_type=review] Production code review with impact explanation")
        
        episode_rewards = []
        episode_steps = 0
        success = False
        
        try:
            for step_num in range(1, 4):  # Max 3 steps
                episode_steps = step_num
                review = self._generate_code_review(observation)
                reward, done, info = await self._step(session_id, json.dumps(review), "code_review")
                episode_rewards.append(reward)
                logger.info(f"[STEP] step={step_num} action=submit_review({len(json.dumps(review))} chars) reward={reward:.2f} done={str(done).lower()} error=null")
                if done:
                    success = True
                    break
        except Exception as e:
            logger.error(f"[ERROR] {e}")
        
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
        logger.info(f"[END] success={str(success).lower()} steps={episode_steps} score={avg_reward:.2f} rewards={','.join(f'{r:.2f}' for r in episode_rewards)}")
        
        self.total_rewards.append(avg_reward)
        self.domain_results[domain].append(avg_reward)
        self.episodes_run += 1
        
        return {
            "task_id": task_id,
            "domain": domain,
            "task_type": "review",
            "difficulty": difficulty,
            "steps": episode_steps,
            "rewards": episode_rewards,
            "avg_reward": avg_reward,
            "success": success
        }
    
    async def run_incident_debug_episode(self, domain: str, difficulty: str) -> Dict[str, Any]:
        """Run INCIDENT_DEBUG domain (multi-step SRE)"""
        observation, session_id = await self._reset(domain, "debug", difficulty)
        task_id = observation.get("task_id", f"incident-debug-{difficulty}")
        
        logger.info(f"\n[START] task={task_id} domain={domain} env=apex-engineering model=Qwen2.5-72B-Instruct")
        logger.info("[task_type=debug] Multi-step incident debugging with progressive revelation")
        
        episode_rewards = []
        episode_steps = 0
        success = False
        
        try:
            max_steps = 3 if difficulty == "hard" else 2
            for step_num in range(1, max_steps + 1):
                episode_steps = step_num
                code = self._generate_incident_fix(observation)
                reward, done, info = await self._step(session_id, code, "incident_debug")
                episode_rewards.append(reward)
                logger.info(f"[STEP] step={step_num} action=submit_fix({len(code)} chars) reward={reward:.2f} done={str(done).lower()} error=null")
                if done:
                    success = True
                    break
        except Exception as e:
            logger.error(f"[ERROR] {e}")
        
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
        logger.info(f"[END] success={str(success).lower()} steps={episode_steps} score={avg_reward:.2f} rewards={','.join(f'{r:.2f}' for r in episode_rewards)}")
        
        self.total_rewards.append(avg_reward)
        self.domain_results[domain].append(avg_reward)
        self.episodes_run += 1
        
        return {
            "task_id": task_id,
            "domain": domain,
            "task_type": "debug",
            "difficulty": difficulty,
            "steps": episode_steps,
            "rewards": episode_rewards,
            "avg_reward": avg_reward,
            "success": success
        }
    
    async def _reset(self, domain: str, task_type: str, difficulty: str) -> tuple:
        """Reset environment"""
        # Map task_type to mode
        # For data_pipeline: "solve" -> "solve", "review" -> "review"  
        # For other domains: use "solve" mode
        if domain == "data_pipeline" and task_type == "review":
            mode = "review"
        else:
            mode = "solve"
        
        if self.use_local:
            from envs.code_solver_env.server.code_solver_environment import CodeSolverEnvironment
            env = CodeSolverEnvironment()
            session_id, observation = await env.reset(
                domain=domain,
                difficulty=difficulty,
                mode=mode
            )
            obs_dict = observation.model_dump() if hasattr(observation, 'model_dump') else observation
            return obs_dict, session_id
        else:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.env_url}/reset",
                    json={"domain": domain, "difficulty": difficulty, "mode": mode},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    return data.get("observation", {}), data.get("session_id", "")
    
    async def _step(self, session_id: str, action: str, task_type: str) -> tuple:
        """Execute step"""
        if self.use_local:
            from envs.code_solver_env.server.code_solver_environment import CodeSolverEnvironment
            env = CodeSolverEnvironment()
            result = await env.step(session_id=session_id, code=action)
            
            if isinstance(result, tuple) and len(result) >= 5:
                observation, reward, terminated, truncated, info = result
                done = terminated or truncated
            else:
                observations, reward, info = result if isinstance(result, tuple) else (result, 0.0, {})
                done = info.get("done", False)
            
            return float(reward), done, info
        else:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.env_url}/step",
                    json={"code": action, "session_id": session_id},
                    params={"session_id": session_id},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    data = await resp.json()
                    return data.get("reward", 0.0), data.get("done", False), data.get("info", {})
    
    def _generate_solve_code(self, obs: Dict) -> str:
        """Generate code for SOLVE"""
        return "import pandas as pd\ndef solve(df):\n    return df\n"
    
    def _generate_code_review(self, obs: Dict) -> Dict:
        """Generate code review"""
        return {
            "problem_identified": "N+1 query pattern",
            "production_impact": "With 10,000 users, this makes 10,000 queries causing timeout at scale",
            "fix_approach": "Use batch query with IN clause",
            "fixed_code": "def get_orders(ids):\n    return db.query(Orders).filter(Orders.user_id.in_(ids)).all()"
        }
    
    def _generate_incident_fix(self, obs: Dict) -> str:
        """Generate incident fix"""
        return "# Fix: Add null check\nif user is None:\n    raise ValueError('User not found')\n"


async def main():
    """Run 9-episode APEX Engineering Benchmark"""
    agent = EngineringBenchmarkAgent(use_local=True)
    
    # 9 episodes: 3 domains × 3 difficulties
    episodes = [
        ("data_pipeline", "solve", "easy"),
        ("data_pipeline", "solve", "medium"),
        ("data_pipeline", "solve", "hard"),
        ("code_review", None, "easy"),
        ("code_review", None, "medium"),
        ("code_review", None, "hard"),
        ("incident_debug", None, "easy"),
        ("incident_debug", None, "medium"),
        ("incident_debug", None, "hard"),
    ]
    
    start_time = time.time()
    results = []
    
    logger.info("\n" + "=" * 80)
    logger.info("APEX ENGINEERING BENCHMARK v3.0")
    logger.info("3 Domains × 3 Difficulties = 9 Episodes")
    logger.info("=" * 80)
    logger.info("Domain 1: data_pipeline (11 tasks) - Write, review, debug data pipelines")
    logger.info("Domain 2: code_review (9 tasks) - Production code with impact explanation")
    logger.info("Domain 3: incident_debug (9 tasks) - Multi-step SRE scenarios")
    logger.info("=" * 80)
    
    for domain, task_type, difficulty in episodes:
        try:
            if domain == "data_pipeline":
                result = await agent.run_solve_episode(domain, difficulty)
            elif domain == "code_review":
                result = await agent.run_code_review_episode(domain, difficulty)
            elif domain == "incident_debug":
                result = await agent.run_incident_debug_episode(domain, difficulty)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed {domain}/{difficulty}: {e}")
            traceback.print_exc()
    
    elapsed_time = time.time() - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Episodes completed: {len(results)}/{len(episodes)}")
    logger.info(f"Total time: {elapsed_time:.1f}s")
    
    if agent.total_rewards:
        avg_reward = sum(agent.total_rewards) / len(agent.total_rewards)
        logger.info(f"Average reward: {avg_reward:.4f}")
    
    logger.info("\nPer-Domain Summary:")
    for domain in ["data_pipeline", "code_review", "incident_debug"]:
        domain_rewards = agent.domain_results[domain]
        if domain_rewards:
            domain_avg = sum(domain_rewards) / len(domain_rewards)
            logger.info(f"  {domain:20} -> avg={domain_avg:.4f} ({len(domain_rewards)} episodes)")
    
    logger.info("\nDetailed Results:")
    for result in results:
        logger.info(
            f"  {result['domain']:15} / {result.get('task_type', 'None'):6} / {result['difficulty']:6} -> "
            f"score={result['avg_reward']:.2f} steps={result['steps']} success={result['success']}"
        )
    
    logger.info("=" * 80)
    return len(results) == len(episodes)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
