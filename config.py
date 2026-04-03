"""
APEX Configuration Loader

Loads configuration from openenv.yaml and overlays environment variables.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Load and manage APEX configuration."""
    
    @staticmethod
    def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file with environment variable overrides.
        
        Args:
            config_file: Path to config file (default: openenv.yaml)
            
        Returns:
            Configuration dictionary
        """
        # Determine config file path
        if config_file is None:
            config_file = Path(__file__).parent / "openenv.yaml"
        else:
            config_file = Path(config_file)
        
        # Load YAML file
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Apply environment variable overrides
        config = ConfigLoader._apply_env_overrides(config)
        
        return config
    
    @staticmethod
    def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Supports overriding:
        - config['inference']['api_base_url'] via API_BASE_URL
        - config['inference']['model_name'] via MODEL_NAME
        - config['inference']['hf_token'] via HF_TOKEN
        - config['server']['port'] via SERVER_PORT
        - config['logging']['level'] via LOG_LEVEL
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration dictionary with env overrides applied
        """
        # Ensure structure exists
        if 'inference' not in config:
            config['inference'] = {}
        if 'server' not in config:
            config['server'] = {}
        if 'logging' not in config:
            config['logging'] = {}
        
        # Apply inference overrides
        if 'API_BASE_URL' in os.environ:
            config['inference']['api_base_url'] = os.getenv('API_BASE_URL')
        
        if 'MODEL_NAME' in os.environ:
            config['inference']['model_name'] = os.getenv('MODEL_NAME')
        
        if 'HF_TOKEN' in os.environ:
            config['inference']['hf_token'] = os.getenv('HF_TOKEN')
        
        # Apply server overrides
        if 'SERVER_PORT' in os.environ:
            try:
                config['server']['port'] = int(os.getenv('SERVER_PORT'))
            except ValueError:
                pass
        
        # Apply logging overrides
        if 'LOG_LEVEL' in os.environ:
            config['logging']['level'] = os.getenv('LOG_LEVEL')
        
        return config
    
    @staticmethod
    def get_inference_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Get inference configuration."""
        return config.get('inference', {})
    
    @staticmethod
    def get_server_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Get server configuration."""
        return config.get('server', {})
    
    @staticmethod
    def get_logging_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Get logging configuration."""
        return config.get('logging', {})


def main():
    """Test config loading."""
    import json
    
    print("Loading configuration...")
    try:
        config = ConfigLoader.load_config()
        print("✅ Configuration loaded successfully!")
        print(json.dumps(config, indent=2))
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
