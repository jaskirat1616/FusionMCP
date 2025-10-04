"""
Command Executor for FusionMCP

This module validates and safely executes AI-generated Fusion 360 scripts.
It includes functionality to prevent destructive operations and logs all
executed commands and errors.
"""

import ast
import logging
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional, Any
from io import StringIO
import traceback


class ScriptValidator:
    """Validates Fusion 360 scripts to prevent potentially destructive operations."""
    
    # Dangerous functions that could cause harm (outside of Fusion 360 context)
    DANGEROUS_FUNCTIONS = {
        'os.remove', 'os.rmdir', 'shutil.rmtree', 'subprocess.call',
        'subprocess.run', 'exec', 'eval', '__import__', 'open'
    }
    
    # Dangerous imports that could cause harm (outside of Fusion 360 context)
    DANGEROUS_IMPORTS = {
        'subprocess', 'sys', 'importlib', 'urllib', 
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


class CommandExecutor:
    """Executes validated Fusion 360 scripts safely."""
    
    def __init__(self, log_path: str = "execution_log.txt"):
        self.validator = ScriptValidator()
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
    
    def execute_script(self, script: str, fusion_app: Any = None) -> Dict[str, Any]:
        """
        Execute a Fusion 360 script after validation.
        
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
            # Create a restricted execution environment
            # For Fusion 360 scripts, we want to ensure they have access to Fusion API
            # while preventing access to dangerous operations
            
            # Capture stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Prepare the execution environment
            # In a real Fusion 360 environment, 'app' would be available
            exec_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'frozenset': frozenset,
                    'type': type,
                    'isinstance': isinstance,
                    'issubclass': issubclass,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'delattr': delattr,
                    'dir': dir,
                    'vars': vars,
                    'id': id,
                    'hash': hash,
                    'callable': callable,
                    'iter': iter,
                    'next': next,
                    'reversed': reversed,
                    'sorted': sorted,
                    'all': all,
                    'any': any,
                    'divmod': divmod,
                    'pow': pow,
                    'chr': chr,
                    'ord': ord,
                    'hex': hex,
                    'oct': oct,
                    'bin': bin,
                    'complex': complex,
                    'property': property,
                    'staticmethod': staticmethod,
                    'classmethod': classmethod,
                    'super': super,
                    'object': object,
                    '__import__': __import__,
                }
            }
            
            # Add Fusion 360 API access if available
            if fusion_app:
                exec_globals['app'] = fusion_app
                # Add common Fusion 360 API modules if they exist
                try:
                    import adsk.core
                    import adsk.fusion
                    exec_globals['adsk'] = adsk
                    exec_globals['core'] = adsk.core
                    exec_globals['fusion'] = adsk.fusion
                except ImportError:
                    pass  # Don't add if not available in this environment
            else:
                # In non-Fusion 360 environment, provide mock Fusion 360 modules for testing
                # This allows us to validate and partially test Fusion 360 scripts without full Fusion 360
                # Since the imports in the script will try to import 'adsk.core' etc., we need to make 
                # sure these are available before the script executes. We'll add them to exec_globals.
                
                # Create mock objects for testing if adsk is not available
                class MockModule:
                    def __init__(self, name="MockModule"):
                        self._name = name
                    
                    def __getattr__(self, name):
                        if name.startswith('__'):
                            raise AttributeError(name)
                        # Return a callable that does nothing but can also have attributes
                        result = lambda *args, **kwargs: MockModule(f"{self._name}.{name}")
                        result.__name__ = name
                        return result

                # Create mock adsk module
                mock_adsk = MockModule("adsk")
                mock_adsk.core = MockModule("adsk.core")
                mock_adsk.fusion = MockModule("adsk.fusion") 
                mock_adsk.cam = MockModule("adsk.cam")
                
                # Add the mock modules to globals before execution so imports succeed
                exec_globals['adsk'] = mock_adsk
                exec_globals['core'] = mock_adsk.core
                exec_globals['fusion'] = mock_adsk.fusion
                exec_globals['cam'] = mock_adsk.cam
            
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
                'timestamp': time.time()
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


# Example usage
if __name__ == "__main__":
    executor = CommandExecutor()
    
    # Example safe script
    safe_script = """
import adsk.core
import adsk.fusion

def create_cube():
    print("Creating a cube...")
    # In real Fusion 360 environment, this would create a cube
    print("Cube created successfully!")

create_cube()
"""
    
    result = executor.execute_script(safe_script)
    print("Execution result:", result)