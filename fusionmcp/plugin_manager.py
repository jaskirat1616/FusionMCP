"""
Plugin Manager for FusionMCP

This module manages external software or API integrations that the AI
can decide to call based on user requests. It provides a registry for
plugins and handles their execution.
"""

import importlib
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from .config import load_config


class Plugin(ABC):
    """Abstract base class for plugins."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin with given parameters."""
        pass


class ExternalAppPlugin(Plugin):
    """Plugin that executes external applications."""
    
    def __init__(self, name: str, description: str, command: str, args: List[str] = None):
        super().__init__(name, description)
        self.command = command
        self.args = args or []
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the external application."""
        try:
            cmd = [self.command] + self.args
            # Replace placeholders in command with actual parameters
            formatted_cmd = []
            for part in cmd:
                formatted_part = part
                for key, value in params.items():
                    placeholder = f"{{{key}}}"
                    if isinstance(value, str):
                        formatted_part = formatted_part.replace(placeholder, value)
                    else:
                        formatted_part = formatted_part.replace(placeholder, str(value))
                formatted_cmd.append(formatted_part)
            
            result = subprocess.run(
                formatted_cmd,
                capture_output=True,
                text=True,
                timeout=params.get('timeout', 30)
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }


class WebAPIPlugin(Plugin):
    """Plugin that calls external web APIs."""
    
    def __init__(self, name: str, description: str, base_url: str, headers: Dict[str, str] = None):
        super().__init__(name, description)
        self.base_url = base_url
        self.headers = headers or {}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the web API."""
        import requests
        
        try:
            method = params.get('method', 'GET').upper()
            endpoint = params.get('endpoint', '')
            url = f"{self.base_url}{endpoint}"
            
            request_params = {
                'headers': {**self.headers, **params.get('headers', {})},
                'timeout': params.get('timeout', 30)
            }
            
            if method == 'GET':
                request_params['params'] = params.get('query_params', {})
            elif method in ['POST', 'PUT', 'PATCH']:
                request_params['json'] = params.get('body', {})
            
            response = requests.request(method, url, **request_params)
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response': response.json() if response.content else None,
                'headers': dict(response.headers)
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'response': None,
                'error': str(e)
            }


class PluginManager:
    """Manages registration and execution of plugins."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.plugins: Dict[str, Plugin] = {}
        self.config = load_config(config_path)
        self._load_plugins_from_config()
    
    def _load_plugins_from_config(self):
        """Load plugins based on configuration."""
        plugins_config = self.config.get('plugins', [])
        
        for plugin_config in plugins_config:
            plugin_type = plugin_config.get('type')
            name = plugin_config.get('name')
            description = plugin_config.get('description', '')
            
            if plugin_type == 'external_app':
                command = plugin_config.get('command')
                args = plugin_config.get('args', [])
                plugin = ExternalAppPlugin(name, description, command, args)
            elif plugin_type == 'web_api':
                base_url = plugin_config.get('base_url')
                headers = plugin_config.get('headers', {})
                plugin = WebAPIPlugin(name, description, base_url, headers)
            else:
                continue  # Unsupported plugin type
            
            self.register_plugin(plugin)
    
    def register_plugin(self, plugin: Plugin):
        """Register a new plugin."""
        self.plugins[plugin.name] = plugin
    
    def unregister_plugin(self, name: str):
        """Unregister a plugin."""
        if name in self.plugins:
            del self.plugins[name]
    
    def execute_plugin(self, name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a plugin by name."""
        if name not in self.plugins:
            return {
                'success': False,
                'error': f"Plugin '{name}' not found"
            }
        
        return self.plugins[name].execute(params)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins."""
        return list(self.plugins.keys())
    
    def get_plugin_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get information about a specific plugin."""
        if name not in self.plugins:
            return None
        
        plugin = self.plugins[name]
        return {
            'name': plugin.name,
            'description': plugin.description,
            'type': type(plugin).__name__
        }
    
    def execute_plugin_if_appropriate(self, request: str) -> Optional[Dict[str, Any]]:
        """Execute a plugin if the request matches plugin capabilities."""
        # This is a simplified implementation
        # In a real system, this would involve more sophisticated matching
        # possibly using AI to determine which plugin to call
        
        for name, plugin in self.plugins.items():
            # Basic keyword matching
            if name.lower() in request.lower() or plugin.description.lower() in request.lower():
                # Execute with default parameters or parameters extracted from request
                return self.execute_plugin(name, {})
        
        return None


# Example plugins
class FileConverterPlugin(Plugin):
    """Example plugin to convert files between formats."""
    
    def __init__(self):
        super().__init__(
            name="file_converter",
            description="Converts files between different formats (STL, STEP, IGES, etc.)"
        )
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the file conversion."""
        input_file = params.get('input_file')
        output_format = params.get('output_format')
        output_file = params.get('output_file')
        
        if not input_file or not output_format:
            return {
                'success': False,
                'error': 'Missing required parameters: input_file and output_format'
            }
        
        # This is a placeholder implementation
        # In reality, this would call a CAD conversion tool
        try:
            # Simulate file conversion
            result = f"Converted {input_file} to {output_format} format as {output_file or 'default_output.' + output_format.lower()}"
            return {
                'success': True,
                'result': result,
                'output_file': output_file or f"converted.{output_format.lower()}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class MaterialDatabasePlugin(Plugin):
    """Example plugin to query material properties."""
    
    def __init__(self):
        super().__init__(
            name="material_database",
            description="Provides access to material properties database"
        )
        # Simulated material database
        self.materials = {
            'aluminum': {
                'density': 2.7,  # g/cm³
                'tensile_strength': 90,  # MPa
                'yield_strength': 55,  # MPa
                'youngs_modulus': 70,  # GPa
                'poissons_ratio': 0.33
            },
            'steel': {
                'density': 7.85,
                'tensile_strength': 400,
                'yield_strength': 250,
                'youngs_modulus': 200,
                'poissons_ratio': 0.27
            },
            'plastic': {
                'density': 1.2,
                'tensile_strength': 50,
                'yield_strength': 30,
                'youngs_modulus': 2.5,
                'poissons_ratio': 0.35
            }
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query material properties."""
        material_name = params.get('material', '').lower()
        
        if material_name in self.materials:
            return {
                'success': True,
                'material': material_name,
                'properties': self.materials[material_name]
            }
        else:
            available = list(self.materials.keys())
            return {
                'success': False,
                'error': f'Material "{material_name}" not found. Available materials: {available}'
            }


# Example usage
if __name__ == "__main__":
    # Create plugin manager
    pm = PluginManager()
    
    # Register example plugins
    pm.register_plugin(FileConverterPlugin())
    pm.register_plugin(MaterialDatabasePlugin())
    
    # List plugins
    print("Available plugins:", pm.list_plugins())
    
    # Execute a plugin
    result = pm.execute_plugin("material_database", {"material": "steel"})
    print("Material database result:", result)
    
    # Execute with request matching
    result = pm.execute_plugin_if_appropriate("I need to convert a file to STL format")
    print("Plugin executed based on request:", result)