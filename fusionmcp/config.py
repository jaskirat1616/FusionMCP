"""
Configuration loader for FusionMCP

This module handles loading configuration from YAML files.
"""

import yaml
import os
from typing import Dict, Any


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration values
    """
    if not os.path.exists(config_path):
        # If config file doesn't exist, return empty dict
        # The system will use environment variables or defaults
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
        return config or {}


# Example usage
if __name__ == "__main__":
    config = load_config()
    print("Configuration loaded:", config)