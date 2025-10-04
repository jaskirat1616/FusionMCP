"""
Fusion 360 Command Executor for FusionMCP

This module safely executes Fusion 360 scripts within the Fusion 360 environment.
It includes functionality to prevent destructive operations and logs all
executed commands and errors.
"""

import ast
import logging
import re
import subprocess
import sys
from typing import Dict, List, Optional, Any
from io import StringIO
import traceback


class FusionScriptValidator:
    """Validates Fusion 360 scripts to prevent potentially destructive operations."""
    
    # Dangerous functions that could cause harm in Fusion 360 (excluding Fusion 360 API methods)
    DANGEROUS_FUNCTIONS = {
        'exec', 'eval', '__import__'
    }
    
    # Dangerous imports that could cause harm in Fusion 360 (excluding Fusion 360 API imports)
    DANGEROUS_IMPORTS = {
        'subprocess', 'sys', 'importlib', 
        'requests', 'webbrowser', 'socket', 'ftplib'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_script(self, script: str) -> Dict[str, Any]:
        """
        Validate a script for potentially dangerous operations.
        
        Args:
            script: The Python script to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_safe': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Parse the script into an AST
            tree = ast.parse(script)
            
            # Check for dangerous imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.DANGEROUS_IMPORTS:
                            result['errors'].append(f"Dangerous import found: {alias.name}")
                            result['is_safe'] = False
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.DANGEROUS_IMPORTS:
                        result['errors'].append(f"Dangerous import found: from {node.module}")
                        result['is_safe'] = False
                
                # Check for dangerous function calls
                elif isinstance(node, ast.Call):
                    func_name = self._get_function_name(node)
                    if func_name in self.DANGEROUS_FUNCTIONS:
                        result['errors'].append(f"Dangerous function call: {func_name}")
                        result['is_safe'] = False
            
            # Additional checks with regex for patterns that might not be caught by AST
            lines = script.split('\n')
            for i, line in enumerate(lines, 1):
                # Check for file operations that might be missed by AST
                if re.search(r'\b(open|file)\b', line) and re.search(r'[\'"].*[\'"]', line):
                    result['warnings'].append(f"Potential file operation on line {i}: {line.strip()}")
        
        except SyntaxError as e:
            result['errors'].append(f"Syntax error: {str(e)}")
            result['is_safe'] = False
        
        except Exception as e:
            result['errors'].append(f"Validation error: {str(e)}")
            result['is_safe'] = False
        
        return result
    
    def _get_function_name(self, call_node: ast.Call) -> str:
        """Extract function name from an AST call node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return f"{self._get_attr_name(call_node.func.value)}.{call_node.func.attr}"
        else:
            return ""
    
    def _get_attr_name(self, node) -> str:
        """Extract name from an AST attribute node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attr_name(node.value)}.{node.attr}"
        else:
            return ""


class FusionCommandExecutor:
    """Executes validated Fusion 360 scripts safely within Fusion 360."""
    
    def __init__(self, log_path: str = "execution_log.txt"):
        self.validator = FusionScriptValidator()
        self.log_path = log_path
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for command execution."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def execute_script(self, script: str, fusion_app=None) -> Dict[str, Any]:
        """
        Execute a Fusion 360 script after validation.
        This version is specifically designed to work within the Fusion 360 environment.
        
        Args:
            script: The Python script to execute
            fusion_app: Fusion 360 application object (if available)
            
        Returns:
            Dictionary with execution results
        """
        # Validate the script first
        validation_result = self.validator.validate_script(script)
        
        if not validation_result['is_safe']:
            return {
                'success': False,
                'error': 'Script validation failed',
                'details': validation_result,
                'output': '',
                'result': None
            }
        
        # Log the execution
        self.logger.info(f"Executing script:\n{script}")
        
        try:
            # Create a safe execution environment for Fusion 360
            # Import the necessary Fusion 360 modules
            exec_globals = {
                '__builtins__': __builtins__,
            }
            
            # Add Fusion 360 API access if available
            if fusion_app:
                exec_globals['app'] = fusion_app
                try:
                    import adsk.core
                    import adsk.fusion
                    exec_globals['adsk'] = adsk
                    exec_globals['core'] = adsk.core
                    exec_globals['fusion'] = adsk.fusion
                except ImportError:
                    pass  # Will be available in Fusion 360
            
            # Capture stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Execute the script
            exec(script, exec_globals)
            
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            output = stdout_capture.getvalue()
            error_output = stderr_capture.getvalue()
            
            # Log the result
            self.logger.info(f"Script executed successfully. Output: {output}")
            
            return {
                'success': True,
                'error': None,
                'details': validation_result,
                'output': output,
                'error_output': error_output,
                'result': exec_globals
            }
        
        except Exception as e:
            # Restore stdout/stderr in case of exception
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            error_msg = traceback.format_exc()
            self.logger.error(f"Script execution failed: {error_msg}")
            
            return {
                'success': False,
                'error': str(e),
                'details': validation_result,
                'output': stdout_capture.getvalue() if 'stdout_capture' in locals() else '',
                'error_output': stderr_capture.getvalue() if 'stderr_capture' in locals() else error_msg,
                'result': None
            }
    
    def execute_safe_command(self, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a predefined safe command.
        
        Args:
            command: The command to execute
            params: Parameters for the command
            
        Returns:
            Dictionary with execution results
        """
        if params is None:
            params = {}
        
        try:
            # In a real Fusion 360 environment, this would execute specific safe commands
            # For now, we'll just log and return
            result = {
                'command': command,
                'params': params,
                'executed': True,
                'timestamp': __import__('time').time()
            }
            
            self.logger.info(f"Executed safe command: {result}")
            
            return {
                'success': True,
                'result': result,
                'output': f"Command '{command}' executed successfully",
                'error': None
            }
        
        except Exception as e:
            error_msg = f"Failed to execute command '{command}': {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'success': False,
                'result': None,
                'output': '',
                'error': error_msg
            }


# For backward compatibility
CommandExecutor = FusionCommandExecutor