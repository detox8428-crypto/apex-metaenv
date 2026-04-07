#!/usr/bin/env python3
"""
APEX Data Pipeline Engineer - Inference & Benchmark
Runs 9-episode benchmark: 3 solve + 3 review + 3 debug across difficulties
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


class DataPipelineAgent:
    """Agent that interacts with APEX Data Pipeline environment"""
    
    def __init__(self, env_url: str = "http://localhost:8000", use_local: bool = True):
        """Initialize agent with environment URL"""
        self.env_url = env_url
        self.use_local = use_local
        self.episodes_run = 0
        self.total_rewards = []
        
        # Import environment if local testing
        if use_local:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "envs", "code_solver_env"))
    
    async def run_solve_episode(self, difficulty: str) -> Dict[str, Any]:
        """Run SOLVE mode episode"""
        task_type = "solve"
        
        # Reset environment
        observation, session_id = await self._reset(task_type, difficulty)
        task_id = observation.get("task_id", f"{difficulty}-{task_type}")
        
        logger.info(f"\n[START] task={task_id} mode={task_type} env=apex-data-pipeline model=Qwen2.5-72B-Instruct")
        
        episode_rewards = []
        episode_steps = 0
        success = False
        
        try:
            for step_num in range(1, 6):
                episode_steps = step_num
                
                # Generate pandas code (simplified placeholder)
                code = self._generate_solve_code(observation)
                
                # Execute step
                reward, done, info = await self._step(session_id, code, task_type)
                episode_rewards.append(reward)
                
                logger.info(f"[STEP] step={step_num} action=submit_code({len(code)} chars) reward={reward:.2f} done={str(done).lower()} error=null")
                
                if done:
                    success = True
                    break
        
        except Exception as e:
            logger.error(f"[ERROR] Episode failed: {e}")
            traceback.print_exc()
        
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
        logger.info(f"[END] success={str(success).lower()} steps={episode_steps} score={avg_reward:.2f} rewards={','.join(f'{r:.2f}' for r in episode_rewards)}")
        
        self.total_rewards.append(avg_reward)
        self.episodes_run += 1
        
        return {
            "task_id": task_id,
            "task_type": task_type,
            "difficulty": difficulty,
            "steps": episode_steps,
            "rewards": episode_rewards,
            "avg_reward": avg_reward,
            "success": success
        }
    
    async def run_review_episode(self, difficulty: str) -> Dict[str, Any]:
        """Run REVIEW mode episode"""
        task_type = "review"
        
        # Reset environment
        observation, session_id = await self._reset(task_type, difficulty)
        task_id = observation.get("task_id", f"{difficulty}-{task_type}")
        
        logger.info(f"\n[START] task={task_id} mode={task_type} env=apex-data-pipeline model=Qwen2.5-72B-Instruct")
        
        episode_rewards = []
        episode_steps = 0
        success = False
        
        try:
            for step_num in range(1, 6):
                episode_steps = step_num
                
                # Generate review JSON
                review = self._generate_review(observation)
                review_str = json.dumps(review)
                
                # Execute step
                reward, done, info = await self._step(session_id, review_str, task_type)
                episode_rewards.append(reward)
                
                logger.info(f"[STEP] step={step_num} action=submit_review({len(review_str)} chars) reward={reward:.2f} done={str(done).lower()} error=null")
                
                if done:
                    success = True
                    break
        
        except Exception as e:
            logger.error(f"[ERROR] Episode failed: {e}")
            traceback.print_exc()
        
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
        logger.info(f"[END] success={str(success).lower()} steps={episode_steps} score={avg_reward:.2f} rewards={','.join(f'{r:.2f}' for r in episode_rewards)}")
        
        self.total_rewards.append(avg_reward)
        self.episodes_run += 1
        
        return {
            "task_id": task_id,
            "task_type": task_type,
            "difficulty": difficulty,
            "steps": episode_steps,
            "rewards": episode_rewards,
            "avg_reward": avg_reward,
            "success": success
        }
    
    async def run_debug_episode(self, difficulty: str) -> Dict[str, Any]:
        """Run DEBUG mode episode"""
        task_type = "debug"
        
        # Reset environment
        observation, session_id = await self._reset(task_type, difficulty)
        task_id = observation.get("task_id", f"{difficulty}-{task_type}")
        
        logger.info(f"\n[START] task={task_id} mode={task_type} env=apex-data-pipeline model=Qwen2.5-72B-Instruct")
        
        episode_rewards = []
        episode_steps = 0
        success = False
        
        try:
            for step_num in range(1, 6):
                episode_steps = step_num
                
                # Generate fixed code
                code = self._generate_debug_fix(observation)
                
                # Execute step
                reward, done, info = await self._step(session_id, code, task_type)
                episode_rewards.append(reward)
                
                logger.info(f"[STEP] step={step_num} action=submit_code({len(code)} chars) reward={reward:.2f} done={str(done).lower()} error=null")
                
                if done:
                    success = True
                    break
        
        except Exception as e:
            logger.error(f"[ERROR] Episode failed: {e}")
            traceback.print_exc()
        
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
        logger.info(f"[END] success={str(success).lower()} steps={episode_steps} score={avg_reward:.2f} rewards={','.join(f'{r:.2f}' for r in episode_rewards)}")
        
        self.total_rewards.append(avg_reward)
        self.episodes_run += 1
        
        return {
            "task_id": task_id,
            "task_type": task_type,
            "difficulty": difficulty,
            "steps": episode_steps,
            "rewards": episode_rewards,
            "avg_reward": avg_reward,
            "success": success
        }

# =========================================================================
    # Private Methods
    # =========================================================================
    
    async def _reset(self, task_type: str, difficulty: str) -> tuple:
        """Reset environment and get observation"""
        if self.use_local:
            from envs.code_solver_env.server.code_solver_environment import CodeSolverEnvironment
            from envs.code_solver_env.models import PipelineObservation
            
            env = CodeSolverEnvironment()
            session_id, observation = await env.reset(
                difficulty=difficulty,
                mode="standard"
            )
            
            # Convert observation to dict if needed
            if hasattr(observation, 'model_dump'):
                obs_dict = observation.model_dump()
            else:
                obs_dict = observation if isinstance(observation, dict) else {}
            
            return obs_dict, session_id
        else:
            # Remote HTTP call
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.env_url}/reset",
                    json={"difficulty": difficulty, "mode": "standard"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    return data.get("observation", {}), data.get("session_id", "")
    
    async def _step(self, session_id: str, action: str, task_type: str) -> tuple:
        """Execute step and return reward, done, info"""
        if self.use_local:
            from envs.code_solver_env.server.code_solver_environment import CodeSolverEnvironment
            from envs.code_solver_env.models import PipelineAction
            
            env = CodeSolverEnvironment()
            
            code_action = PipelineAction(code=action, session_id=session_id)
            result = await env.step(
                session_id=session_id,
                code=action
            )
            
            if isinstance(result, tuple) and len(result) >= 5:
                observation, reward, terminated, truncated, info = result
            else:
                observation, reward, info = result if isinstance(result, tuple) else (result, 0.0, {})
                terminated = False
                truncated = False
            
            done = terminated or truncated or info.get("done", False)
            
            return float(reward), done, info
        else:
            # Remote HTTP call
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.env_url}/step",
                    json={"code": action, "session_id": session_id},
                    params={"session_id": session_id},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    data = await resp.json()
                    return (
                        data.get("reward", 0.0),
                        data.get("done", False),
                        data.get("info", {})
                    )
    
    def _generate_solve_code(self, observation: Dict[str, Any]) -> str:
        """Generate code for SOLVE task"""
        # Placeholder: in production, call LLM
        return """import pandas as pd
def solve(df):
    # Placeholder solution
    return df
"""
    
    def _generate_review(self, observation: Dict[str, Any]) -> Dict[str, str]:
        """Generate review for REVIEW task"""
        # Placeholder: in production, call LLM to analyze bug
        return {
            "bug_location": "line 5",
            "bug_type": "wrong_aggregation",
            "explanation": "The aggregation function is incorrect",
            "fixed_code": "def fixed(df):\n    return df.groupby('id').sum()"
        }
    
    def _generate_debug_fix(self, observation: Dict[str, Any]) -> str:
        """Generate fix for DEBUG task"""
        # Placeholder: in production, call LLM to fix error
        return """import pandas as pd
def fixed(df):
    # Attempt to fix the error
    return df.fillna(0)
"""



async def main():
    """Main benchmark function"""
    logger.info("=" * 70)
    logger.info("APEX Data Pipeline Engineer - Inference Benchmark")
    logger.info("=" * 70)
    
    # Initialize agent
    agent = DataPipelineAgent(use_local=True)
    
    # Episode configuration: (task_type, difficulty)
    episodes = [
        ("solve", "easy"),
        ("solve", "medium"),
        ("solve", "hard"),
        ("review", "easy"),
        ("review", "medium"),
        ("review", "hard"),
        ("debug", "easy"),
        ("debug", "medium"),
        ("debug", "hard"),
    ]
    
    start_time = time.time()
    results = []
    
    for task_type, difficulty in episodes:
        try:
            if task_type == "solve":
                result = await agent.run_solve_episode(difficulty)
            elif task_type == "review":
                result = await agent.run_review_episode(difficulty)
            else:  # debug
                result = await agent.run_debug_episode(difficulty)
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Failed to run {task_type}/{difficulty} episode: {e}")
            traceback.print_exc()
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info(f"Benchmark Summary")
    logger.info("=" * 70)
    logger.info(f"Episodes completed: {len(results)}/{len(episodes)}")
    logger.info(f"Total time: {elapsed_time:.1f}s")
    
    if agent.total_rewards:
        avg_reward = sum(agent.total_rewards) / len(agent.total_rewards)
        logger.info(f"Average reward: {avg_reward:.4f}")
    
    logger.info("\nDetailed Results:")
    for result in results:
        logger.info(
            f"  {result['task_type']:6} / {result['difficulty']:6} -> "
            f"steps={result['steps']} avg_reward={result['avg_reward']:.2f} success={result['success']}"
        )
    
    logger.info("=" * 70)
    
    return len(results) == len(episodes)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
