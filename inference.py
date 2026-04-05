"""
Code Solver RL Environment - Inference Module

Provides AI-powered code generation for solving LeetCode-style problems.
Integrates with OpenAI, Claude, or compatible LLM services.
"""

import os
import json
import logging
import sys
import requests
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code_solver.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class CodeSolverAgent:
    """AI Agent for solving coding problems using LLM inference."""
    
    def __init__(self, model: str = None, api_key: str = None, api_base_url: str = None, env_url: str = None):
        """
        Initialize the Code Solver Agent.
        
        Args:
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo', defaults to env var)
            api_key: API key for LLM service (HF_TOKEN, defaults to env vars)
            api_base_url: Base URL for LLM API (defaults to env var)
            env_url: URL for code solver environment server (default http://localhost:8000)
        """
        self.model = model or os.getenv('MODEL_NAME', 'Qwen/Qwen2.5-Coder-32B-Instruct')
        self.api_key = api_key or os.getenv('HF_TOKEN', '')
        self.api_base_url = api_base_url or os.getenv('API_BASE_URL', 'https://router.huggingface.co/v1')
        self.env_url = env_url or os.getenv('ENV_URL', 'http://localhost:8000')
        
        # State tracking
        self.current_problem = None
        self.session_id = None
        self.submission_history = []
        
        logger.info(f"Initialized CodeSolverAgent")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  Environment server: {self.env_url}")

    def reset(self) -> Dict[str, Any]:
        """
        Reset the environment and get a new problem.
        
        Returns:
            Observation with problem details
        """
        try:
            response = requests.post(
                f"{self.env_url}/reset",
                json={},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract observation and session_id from response
            self.current_problem = result.get('observation', {})
            self.session_id = result.get('session_id')
            self.submission_history = []
            
            logger.info(f"Reset environment - Got problem: {self.current_problem.get('title', 'Unknown')}")
            return self.current_problem
        except requests.exceptions.RequestException as e:
            logger.error(f"Error resetting environment: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in reset: {e}")
            return {}

    def generate_solution(
        self,
        observation: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate Python code solution using LLM (OpenAI or HF Inference API).
        
        Args:
            observation: Problem observation with description, examples, etc.
            feedback: Optional feedback from previous failed attempt
            temperature: LLM temperature for generation
            
        Returns:
            Python code as string
        """
        # Build prompt
        prompt = self._build_solution_prompt(observation, feedback)
        
        logger.info(f"Generating solution for: {observation.get('title', 'Unknown')}")
        
        try:
            # Use OpenAI-compatible API (works for both OpenAI and HF router)
            return self._generate_openai(prompt, temperature)
        except Exception as e:
            logger.error(f"Error generating solution: {e}")
            return self._get_template_solution(observation)

    def _generate_openai(self, prompt: str, temperature: float) -> str:
        """Generate code using OpenAI API or HF Router API."""
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=self.api_base_url,
                api_key=self.api_key
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python programmer. Generate clean, efficient code solutions for coding problems."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=temperature,
                timeout=30
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown if needed
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            logger.info(f"Generated solution ({len(code)} chars) via OpenAI")
            return code
            
        except ImportError:
            logger.warning("OpenAI library not installed, trying requests fallback")
            return self._generate_openai_requests(prompt, temperature)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def _generate_openai_requests(self, prompt: str, temperature: float) -> str:
        """Generate code using OpenAI API via requests library."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert Python programmer. Generate clean, efficient code solutions for coding problems."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": temperature
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            raise Exception(f"OpenAI API returned {response.status_code}")
        
        result = response.json()
        code = result['choices'][0]['message']['content']
        
        # Extract code from markdown if needed
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        logger.info(f"Generated solution ({len(code)} chars) via OpenAI API")
        return code

    def _generate_huggingface(self, prompt: str, temperature: float) -> str:
        """Generate code using HuggingFace Inference API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Map model names to HF model IDs if needed
        model_url = f"{self.api_base_url}/{self.model}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 2000,
                "temperature": temperature,
                "do_sample": True,
            }
        }
        
        try:
            response = requests.post(
                model_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 403:
                logger.warning("HF token may not have inference permission. Try enabling 'Make calls to Inference Providers' in HF settings.")
                raise Exception("HF token permissions insufficient - enable inference in HF token settings")
            
            if response.status_code != 200:
                logger.error(f"HF API error: {response.status_code} - {response.text}")
                raise Exception(f"HF API returned {response.status_code}")
            
            result = response.json()
            
            # HF returns a list with generated_text
            if isinstance(result, list) and len(result) > 0:
                code = result[0].get('generated_text', '')
            else:
                code = result.get('generated_text', '')
            
            # Extract code from markdown if needed
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            logger.info(f"Generated solution ({len(code)} chars) via HuggingFace")
            return code
            
        except Exception as e:
            logger.error(f"HF API error: {e}")
            raise

    def step(self, code: str) -> Dict[str, Any]:
        """
        Submit code solution to environment.
        
        Args:
            code: Python code to submit
            
        Returns:
            Step result with reward, feedback, test results
        """
        try:
            if not self.session_id:
                logger.error("No session ID - must call reset() first")
                return {
                    'observation': self.current_problem,
                    'reward': 0.0,
                    'terminated': False,
                    'truncated': False,
                    'info': {'error': 'No session'}
                }
            
            logger.debug(f"Submitting code to {self.env_url}/step")
            logger.debug(f"Request body: code={len(code)} chars, session_id={self.session_id}")
            
            response = requests.post(
                f"{self.env_url}/step",
                json={
                    "code": code,
                    "session_id": self.session_id
                },
                timeout=15
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            # Track submission
            self.submission_history.append({
                'code': code,
                'reward': result.get('reward', 0.0),
                'passed': result.get('info', {}).get('passed_cases', 0),
                'total': result.get('info', {}).get('total_cases', 0),
                'error': result.get('info', {}).get('error_message')
            })
            
            passed = result.get('info', {}).get('passed_cases', 0)
            total = result.get('info', {}).get('total_cases', 0)
            reward = result.get('reward', 0.0)
            logger.info(f"Submission result: {reward:.2f} reward ({passed}/{total} tests)")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting code: {e}")
            return {
                'observation': self.current_problem,
                'reward': 0.0,
                'terminated': False,
                'truncated': False,
                'info': {'error': str(e)}
            }
        except Exception as e:
            logger.error(f"Unexpected error in step: {e}")
            return {
                'observation': self.current_problem,
                'reward': 0.0,
                'terminated': False,
                'truncated': False,
                'info': {'error': str(e)}
            }

    def _build_solution_prompt(self, observation: Dict[str, Any], feedback: Optional[Dict[str, Any]] = None) -> str:
        """Build the prompt for code generation."""
        prompt = f"""Solve this coding problem:

Title: {observation.get('title', 'Unknown')}

Description:
{observation.get('description', 'No description')}

Function Signature:
{observation.get('function_signature', '')}

Examples:
{observation.get('examples', 'No examples')}

Constraints:
{observation.get('constraints', 'No constraints')}

Difficulty: {observation.get('difficulty', 'Unknown')}
"""
        
        if feedback and feedback.get('error'):
            prompt += f"\nPrevious attempt error:\n{feedback['error']}\n"
            prompt += f"Tests passed: {feedback.get('passed', 0)}/{feedback.get('total', 0)}\n"
            prompt += "Please fix the issues and provide a corrected solution.\n"
        
        prompt += "\nProvide ONLY the Python code without any explanations or markdown. Write complete, working code that can be executed."
        return prompt

    def _build_review_prompt(self, observation: Dict[str, Any]) -> str:
        """Build the prompt for code review (fixing buggy code)."""
        prompt = f"""You are an expert Python code reviewer.

Task: {observation.get('title', 'Unknown')}

{observation.get('description', 'No description')}

The code above contains a bug. Analyze it carefully and return ONLY the complete fixed Python function with the bug corrected. No explanation, no markdown, just the fixed function starting with 'def'."""
        return prompt

    def generate_fix(self, observation: Dict[str, Any], temperature: float = 0.7) -> str:
        """
        Generate a fixed version of buggy code (for code review mode).
        
        Args:
            observation: Problem observation with buggy code in description
            temperature: LLM temperature for generation
            
        Returns:
            Fixed Python code as string
        """
        prompt = self._build_review_prompt(observation)
        
        logger.info(f"Generating fix for: {observation.get('title', 'Unknown')}")
        
        try:
            return self._generate_openai(prompt, temperature)
        except Exception as e:
            logger.error(f"Error generating fix: {e}")
            return self._get_template_solution(observation)

    def _get_template_solution(self, observation: Dict[str, Any]) -> str:
        """Get a template solution when LLM is not available."""
        sig = observation.get('function_signature', '').strip()
        if sig:
            return f"{sig}\n    pass  # TODO: Implement solution"
        return "def solution(*args, **kwargs):\n    pass  # TODO: Implement solution"



def main():
    """Main function demonstrating Code Solver Agent capabilities with solve and review modes."""
    
    # Initialize agent
    agent = CodeSolverAgent(
        model=os.getenv('MODEL_NAME', 'Qwen/Qwen2.5-72B-Instruct'),
        api_key=os.getenv('HF_TOKEN', ''),
        api_base_url=os.getenv('API_BASE_URL', 'https://router.huggingface.co/v1'),
        env_url=os.getenv('ENV_URL', 'http://localhost:8000')
    )
    
    # Define episodes: 3 solve + 3 review
    EPISODES = [
        {"mode": "solve", "difficulty": "easy", "task_name": "easy-solve"},
        {"mode": "solve", "difficulty": "medium", "task_name": "medium-solve"},
        {"mode": "solve", "difficulty": "hard", "task_name": "hard-solve"},
        {"mode": "review", "difficulty": "easy", "task_name": "easy-review"},
        {"mode": "review", "difficulty": "medium", "task_name": "medium-review"},
        {"mode": "review", "difficulty": "hard", "task_name": "hard-review"},
    ]
    
    try:
        all_rewards = []
        model_name = os.getenv('MODEL_NAME', 'Qwen/Qwen2.5-72B-Instruct').split('/')[-1]
        
        for episode_idx, episode_config in enumerate(EPISODES):
            mode = episode_config["mode"]
            difficulty = episode_config["difficulty"]
            task_name = episode_config["task_name"]
            
            # Reset with appropriate mode
            agent.current_problem = None
            agent.session_id = None
            
            try:
                response = requests.post(
                    f"{agent.env_url}/reset",
                    json={"difficulty": difficulty, "mode": mode},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                agent.current_problem = result.get('observation', {})
                agent.session_id = result.get('session_id')
            except Exception as e:
                logger.error(f"Failed to reset environment for {task_name}: {e}")
                continue
            
            problem = agent.current_problem
            
            # [START] format
            print(f"[START] task={task_name} mode={mode} env=code-solver-env model={model_name}")
            
            step_count = 0
            episode_rewards = []
            success = False
            
            # Max 3 attempts per problem
            max_attempts = 3
            for attempt in range(max_attempts):
                step_count += 1
                
                try:
                    # Generate code based on mode
                    if mode == "review":
                        code = agent.generate_fix(problem)
                    else:
                        feedback = None
                        if attempt > 0 and agent.submission_history:
                            feedback = agent.submission_history[-1]
                        code = agent.generate_solution(problem, feedback)
                    
                    if not code or len(code.strip()) == 0:
                        logger.warning("Generated code is empty")
                        code = agent._get_template_solution(problem)
                    
                    # Submit code
                    result = agent.step(code)
                    
                    reward = result.get('reward', 0.0)
                    episode_rewards.append(reward)
                    done = result.get('terminated', False) or reward >= 1.0
                    error = result.get('info', {}).get('error_message') or \
                            result.get('info', {}).get('error') or None
                    
                    # [STEP] format
                    action_str = f"submit_code({len(code)} chars)"
                    error_str = f'"{error}"' if error else "null"
                    done_str = "true" if done else "false"
                    print(f"[STEP] step={step_count} action={action_str} reward={reward:.2f} done={done_str} error={error_str}")
                    
                    if done or reward >= 0.99:
                        success = True
                        break
                    
                    # Update problem observation for next iteration
                    if 'observation' in result:
                        problem = result['observation']
                
                except Exception as e:
                    logger.error(f"Error in attempt {attempt + 1}: {e}")
                    error_str = f'"{str(e)}"'
                    done_str = "false"
                    print(f"[STEP] step={step_count} action=generate_code reward=0.0 done={done_str} error={error_str}")
                    
                    if attempt == max_attempts - 1:
                        break
            
            all_rewards.extend(episode_rewards)
            
            # [END] format
            success_str = "true" if success else "false"
            total_reward = sum(episode_rewards) if episode_rewards else 0.0
            print(f"[END] success={success_str} steps={step_count} rewards={total_reward:.2f}")
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Completed {len(EPISODES)} episodes (3 solve + 3 review)")
        if all_rewards:
            avg_reward = sum(all_rewards) / len(all_rewards)
            logger.info(f"Average reward: {avg_reward:.2f}")
            total_reward = sum(all_rewards)
            logger.info(f"Total reward: {total_reward:.2f}")
        else:
            logger.warning("No rewards collected")
        logger.info(f"{'='*60}")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"[END] success=false steps=0 rewards=0.0")
        sys.exit(1)


if __name__ == "__main__":
    main()
