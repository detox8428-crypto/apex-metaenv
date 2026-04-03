"""
APEX Environment - Inference Module

Provides inference capabilities using OpenAI API or compatible services.
Reads configuration from environment variables and logging in required format.
"""

import os
import json
import logging
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('inference.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class APEXInferenceClient:
    """Client for inference operations with APEX Environment."""
    
    def __init__(self):
        """Initialize the inference client with configuration from environment variables."""
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.model_name = os.getenv('MODEL_NAME', 'gpt-3.5-turbo')
        self.hf_token = os.getenv('HF_TOKEN', '')
        
        # Try to import OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY', 'sk-default'),
                base_url=self.api_base_url if 'openai' not in self.api_base_url else None
            )
        except ImportError:
            logger.warning("OpenAI client not available, using mock implementation")
            self.client = None
        
        logger.info(f"Initialized APEXInferenceClient")
        logger.info(f"  API Base URL: {self.api_base_url}")
        logger.info(f"  Model Name: {self.model_name}")
        logger.info(f"  HF Token: {'[SET]' if self.hf_token else '[NOT SET]'}")
    
    def _log_start(self, operation: str, task_id: Optional[str] = None):
        """Log operation start marker."""
        timestamp = datetime.now().isoformat()
        logger.info(f"[START] {operation} (task_id={task_id}, timestamp={timestamp})")
    
    def _log_step(self, step_data: Dict[str, Any]):
        """Log step data with required format."""
        step_info = {
            'timestamp': datetime.now().isoformat(),
            'data': step_data
        }
        logger.info(f"[STEP] {json.dumps(step_info)}")
    
    def _log_end(self, operation: str, result: Dict[str, Any]):
        """Log operation end marker."""
        timestamp = datetime.now().isoformat()
        logger.info(f"[END] {operation} (timestamp={timestamp}, success={result.get('success', False)})")
    
    def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 150,
        temperature: float = 0.7,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the configured model.
        
        Args:
            prompt: The input prompt
            context: Optional context dictionary
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            task_id: Optional task identifier for logging
            
        Returns:
            Dictionary with response and metadata
        """
        self._log_start("generate_response", task_id)
        
        try:
            # Log step: request preparation
            self._log_step({
                'operation': 'generate_response',
                'prompt_length': len(prompt),
                'model': self.model_name,
                'temperature': temperature,
                'max_tokens': max_tokens
            })
            
            # Call inference
            if self.client:
                message_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for the APEX Environment."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30
                )
                
                response_text = message_response.choices[0].message.content
            else:
                # Mock response for testing
                response_text = f"Mock response to: {prompt[:50]}..."
            
            # Log step: response received
            self._log_step({
                'operation': 'inference_complete',
                'response_length': len(response_text),
                'model': self.model_name
            })
            
            result = {
                'success': True,
                'response': response_text,
                'model': self.model_name,
                'prompt_length': len(prompt),
                'response_length': len(response_text),
                'context': context
            }
            
            self._log_end("generate_response", result)
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            
            result = {
                'success': False,
                'error': str(e),
                'model': self.model_name
            }
            
            self._log_end("generate_response", result)
            return result
    
    def classify_action(
        self,
        action_description: str,
        available_actions: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify an action description to determine action type.
        
        Args:
            action_description: Description of the action
            available_actions: List of available action types
            task_id: Optional task identifier
            
        Returns:
            Dictionary with classification result
        """
        self._log_start("classify_action", task_id)
        
        if available_actions is None:
            available_actions = ["email", "meeting", "translation", "gesture", "noop"]
        
        try:
            # Log step: classification start
            self._log_step({
                'operation': 'action_classification',
                'action_description_length': len(action_description),
                'available_actions': available_actions
            })
            
            prompt = f"""Classify the following action description into one of these categories: {', '.join(available_actions)}
            
Action: {action_description}

Respond with ONLY the action type name."""
            
            # Generate classification
            response = self.generate_response(
                prompt=prompt,
                max_tokens=10,
                temperature=0.0,
                task_id=task_id
            )
            
            if response['success']:
                classified_action = response['response'].strip().lower()
                
                # Log step: classification result
                self._log_step({
                    'operation': 'classification_result',
                    'classified_action': classified_action,
                    'valid': classified_action in available_actions
                })
                
                result = {
                    'success': True,
                    'action': classified_action,
                    'is_valid': classified_action in available_actions
                }
            else:
                result = {
                    'success': False,
                    'error': response['error']
                }
            
            self._log_end("classify_action", result)
            return result
            
        except Exception as e:
            logger.error(f"Error classifying action: {str(e)}")
            
            result = {
                'success': False,
                'error': str(e)
            }
            
            self._log_end("classify_action", result)
            return result
    
    def extract_parameters(
        self,
        action_description: str,
        action_type: str,
        schema: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract parameters from action description based on action type.
        
        Args:
            action_description: Description of the action
            action_type: Type of action (email, meeting, etc.)
            schema: Optional schema for parameters
            task_id: Optional task identifier
            
        Returns:
            Dictionary with extracted parameters
        """
        self._log_start("extract_parameters", task_id)
        
        try:
            # Log step: extraction start
            self._log_step({
                'operation': 'parameter_extraction',
                'action_type': action_type,
                'description_length': len(action_description),
                'has_schema': schema is not None
            })
            
            prompt = f"""Extract parameters for the following {action_type} action:

Action description: {action_description}

Return a JSON object with the extracted parameters."""
            
            response = self.generate_response(
                prompt=prompt,
                max_tokens=200,
                temperature=0.0,
                task_id=task_id
            )
            
            if response['success']:
                try:
                    parameters = json.loads(response['response'])
                except json.JSONDecodeError:
                    # Extract JSON from response if it contains extra text
                    import re
                    json_match = re.search(r'\{.*\}', response['response'], re.DOTALL)
                    if json_match:
                        parameters = json.loads(json_match.group())
                    else:
                        parameters = {}
                
                # Log step: parameters extracted
                self._log_step({
                    'operation': 'parameters_extracted',
                    'parameter_count': len(parameters),
                    'action_type': action_type
                })
                
                result = {
                    'success': True,
                    'parameters': parameters,
                    'action_type': action_type
                }
            else:
                result = {
                    'success': False,
                    'error': response['error']
                }
            
            self._log_end("extract_parameters", result)
            return result
            
        except Exception as e:
            logger.error(f"Error extracting parameters: {str(e)}")
            
            result = {
                'success': False,
                'error': str(e)
            }
            
            self._log_end("extract_parameters", result)
            return result


def main():
    """Main function demonstrating inference capabilities."""
    
    logger.info("="*60)
    logger.info("APEX Environment - Inference Module")
    logger.info("="*60)
    
    # Initialize client
    client = APEXInferenceClient()
    
    # Example 1: Generate response
    logger.info("\n--- Example 1: Generate Response ---")
    response = client.generate_response(
        prompt="What is the APEX Environment?",
        context={"domain": "training"},
        task_id="task_001"
    )
    if response['success']:
        print(f"Response: {response['response']}")
    
    # Example 2: Classify action
    logger.info("\n--- Example 2: Classify Action ---")
    classification = client.classify_action(
        action_description="Send an email to john@example.com about the meeting tomorrow",
        task_id="task_002"
    )
    if classification['success']:
        print(f"Classified action: {classification['action']}")
    
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
