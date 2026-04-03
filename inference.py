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
from typing import Optional, Dict, Any, List, Tuple
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
    
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        """
        Initialize the Code Solver Agent.
        
        Args:
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo', defaults to env var)
            api_key: API key for LLM service (defaults to env vars)
            base_url: Base URL for inference server (defaults to localhost:8000)
        """
        self.model = model or os.getenv('MODEL_NAME', 'gpt-4')
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '')
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.server_url = f"{self.base_url}"
        
        # Initialize LLM client
        self.llm_client = None
        self._init_llm_client()
        
        # State tracking
        self.current_problem = None
        self.submission_history = []
        self.revision_count = 0
        
        logger.info(f"Initialized CodeSolverAgent")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  Server: {self.server_url}")
    
    def _init_llm_client(self):
        """Initialize LLM client (OpenAI compatible)."""
        try:
            from openai import OpenAI
            self.llm_client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.openai.com/v1" if "openai" in self.model else None
            )
            logger.info(f"OpenAI client initialized for {self.model}")
        except ImportError:
            logger.warning("OpenAI client not available")
            self.llm_client = None
    
    def reset(self) -> Dict[str, Any]:
        """
        Reset the environment and get a new problem.
        
        Returns:
            Observation with problem details
        """
        try:
            response = requests.post(f"{self.server_url}/reset", timeout=10)
            response.raise_for_status()
            result = response.json()
            self.current_problem = result.get('observation', {})
            self.submission_history = []
            self.revision_count = 0
            
            logger.info(f"Reset environment - Got problem: {self.current_problem.get('title', 'Unknown')}")
            return self.current_problem
        except Exception as e:
            logger.error(f"Error resetting environment: {e}")
            return {}
    
    def generate_solution(
        self,
        observation: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate Python code solution using LLM.
        
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
        
        if not self.llm_client:
            logger.warning("LLM client not available, returning template")
            return self._get_template_solution(observation)
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python programmer. Generate clean, efficient code solutions."
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
            
            logger.info(f"Generated solution ({len(code)} chars)")
            return code
            
        except Exception as e:
            logger.error(f"Error generating solution: {e}")
            return self._get_template_solution(observation)
    
    def step(self, code: str) -> Dict[str, Any]:
        """
        Submit code solution to environment.
        
        Args:
            code: Python code to submit
            
        Returns:
            Step result with reward, feedback, test results
        """
        try:
            response = requests.post(
                f"{self.server_url}/step",
                json={"action": {"code": code}},
                timeout=15
            )
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
            
            logger.info(f"Submission result: {result['reward']:.2f} reward " +
                       f"({result.get('info', {}).get('passed_cases', 0)}/{result.get('info', {}).get('total_cases', 0)} tests)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting code: {e}")
            return {
                'observation': self.current_problem,
                'reward': 0.0,
                'terminated': False,
                'truncated': False,
                'info': {'error': str(e)}
            }
    
    def solve(self, max_attempts: int = 3) -> Tuple[bool, Dict[str, Any]]:
        """
        Attempt to solve the current problem with multiple revisions.
        
        Args:
            max_attempts: Maximum number of attempts
            
        Returns:
            (success: bool, result: dict)
        """
        if not self.current_problem:
            self.reset()
        
        logger.info(f"Starting solve attempt for: {self.current_problem.get('title')}")
        
        for attempt in range(max_attempts):
            logger.info(f"Attempt {attempt + 1}/{max_attempts}")
            
            # Generate solution
            feedback = None
            if attempt > 0 and self.submission_history:
                feedback = self.submission_history[-1]
            
            code = self.generate_solution(self.current_problem, feedback)
            
            # Submit and get result
            result = self.step(code)
            
            # Check if solved
            if result.get('terminated', False) or result.get('reward', 0.0) >= 1.0:
                logger.info(f"✓ Problem solved in {attempt + 1} attempts!")
                return True, result
            
            # Get observation for next iteration
            if 'observation' in result:
                self.current_problem = result['observation']
        
        logger.info(f"✗ Failed to solve after {max_attempts} attempts")
        return False, self.submission_history[-1] if self.submission_history else {}
    
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
        
        prompt += "\nProvide only the Python code without explanations. Use markdown code block if needed."
        return prompt
    
    def _get_template_solution(self, observation: Dict[str, Any]) -> str:
        """Get a template solution when LLM is not available."""
        sig = observation.get('function_signature', '').strip()
        if sig:
            return f"{sig}\n    pass  # TODO: Implement solution"
        return "def solution(*args, **kwargs):\n    pass  # TODO: Implement solution"

def main():
    """Main function demonstrating Code Solver Agent capabilities."""
    
    # Initialize agent
    agent = CodeSolverAgent(
        model=os.getenv('MODEL_NAME', 'gpt-4'),
        api_key=os.getenv('OPENAI_API_KEY', ''),
        base_url=os.getenv('API_BASE_URL', 'http://localhost:8000')
    )
    
    try:
        # Solve multiple problems
        all_rewards = []
        task_names = []
        
        for problem_idx in range(3):  # Solve 3 problems minimum
            # Reset and get new problem
            problem = agent.reset()
            task_name = problem.get('title', f'problem_{problem_idx}')
            task_names.append(task_name)
            
            # [START] format: task=<task_name> env=<benchmark> model=<model_name>
            model_name = os.getenv('MODEL_NAME', 'gpt-4')
            print(f"[START] task={task_name} env=code_solver model={model_name}")
            
            step_count = 0
            episode_rewards = []
            success = False
            last_error = None
            
            for attempt in range(3):  # Max 3 attempts per problem
                step_count += 1
                
                # Generate code
                feedback = None
                if attempt > 0 and agent.submission_history:
                    feedback = agent.submission_history[-1]
                
                code = agent.generate_solution(problem, feedback)
                
                # Submit code
                result = agent.step(code)
                
                reward = result.get('reward', 0.0)
                episode_rewards.append(reward)
                done = result.get('terminated', False) or reward >= 1.0
                error = result.get('info', {}).get('error_message') or \
                        result.get('info', {}).get('error') or None
                last_error = error
                
                # [STEP] format: step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
                action_str = f"submit_code"
                error_str = f'"{error}"' if error else "null"
                done_str = "true" if done else "false"
                print(f"[STEP] step={step_count} action={action_str} reward={reward:.2f} done={done_str} error={error_str}")
                
                if done:
                    success = True
                    break
                
                # Update problem observation for next iteration
                if 'observation' in result:
                    problem = result['observation']
            
            all_rewards.extend(episode_rewards)
            
            # [END] format: success=<true|false> steps=<n> rewards=<r1,r2,...,rn>
            success_str = "true" if success else "false"
            rewards_str = ','.join([f"{r:.2f}" for r in episode_rewards])
            print(f"[END] success={success_str} steps={step_count} rewards={rewards_str}")
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Completed {len(task_names)} problems")
        logger.info(f"Average reward: {sum(all_rewards) / len(all_rewards) if all_rewards else 0:.2f}")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"[END] success=false steps=0 rewards=")


if __name__ == "__main__":
    main()
    
    # Example 3: Extract parameters
    logger.info("\n--- Example 3: Extract Parameters ---")
    parameters = client.extract_parameters(
        action_description="Schedule a meeting with Alice and Bob for tomorrow at 2 PM",
        action_type="meeting",
        task_id="task_003"
    )
    if parameters['success']:
        print(f"Extracted parameters: {json.dumps(parameters['parameters'], indent=2)}")
    
    logger.info("\n" + "="*60)
    logger.info("Inference module test complete")
    logger.info("="*60)


if __name__ == "__main__":
    main()
