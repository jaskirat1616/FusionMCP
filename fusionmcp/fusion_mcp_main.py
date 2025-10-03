"""
FusionMCP Main Module

This is the main orchestrator that brings together all components:
- Context management
- AI interface
- Command execution
- Plugin management
- User interface

This module handles the main interaction loop with users and coordinates
the MCP components to process requests and execute commands in Fusion 360.
"""

import sys
import os
from typing import Dict, Any, Optional

# Import local modules
from .context_manager import ContextManager
from .ai_interface import AIInterface
from .command_executor import CommandExecutor
from .plugin_manager import PluginManager


class FusionMCP:
    """Main FusionMCP orchestrator class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.context_manager = ContextManager()
        self.ai_interface = AIInterface(config_path)
        self.command_executor = CommandExecutor()
        self.plugin_manager = PluginManager(config_path)
        
        # Store Fusion 360 application reference if available
        self.fusion_app = None
        
        # Initialize with basic system prompt
        self.system_context = {
            "system": "You are FusionMCP, an AI assistant integrated with Fusion 360 CAD software. Your role is to interpret user requests and generate appropriate Fusion 360 Python scripts.",
            "capabilities": [
                "Create and modify CAD models",
                "Access to Fusion 360 API",
                "Execute safe operations",
                "Integrate with external plugins"
            ]
        }
    
    def set_fusion_app(self, app):
        """Set the Fusion 360 application object."""
        self.fusion_app = app
    
    def process_request(self, user_request: str) -> Dict[str, Any]:
        """
        Process a user request through the entire MCP pipeline.
        
        Args:
            user_request: Natural language request from the user
            
        Returns:
            Dictionary containing the processing results
        """
        # Add user request to context
        self.context_manager.add_interaction(user_request, "", None)
        
        # Get recent context to provide to the AI
        recent_context = self.context_manager.get_recent_context(5)
        
        # Try to execute a plugin if appropriate
        plugin_result = self.plugin_manager.execute_plugin_if_appropriate(user_request)
        if plugin_result and plugin_result['success']:
            # If a plugin was executed successfully, return the result
            result = {
                'type': 'plugin_result',
                'plugin_result': plugin_result,
                'script_generated': False,
                'execution_result': None
            }
            self.context_manager.add_interaction(
                user_request,
                f"Plugin result: {plugin_result}",
                result
            )
            return result
        
        # Generate Fusion 360 script using AI
        script = self.ai_interface.generate_fusion_script(
            user_request,
            context={"recent_interactions": recent_context}
        )
        
        # Validate and execute the script
        execution_result = self.command_executor.execute_script(script, self.fusion_app)
        
        if not execution_result['success']:
            # If execution failed, ask AI to fix the script
            fixed_script = self.ai_interface.validate_and_fix_script(script, execution_result['error_output'])
            execution_result = self.command_executor.execute_script(fixed_script, self.fusion_app)
        
        # Add to context
        self.context_manager.add_interaction(
            user_request,
            script,
            execution_result
        )
        
        return {
            'type': 'fusion_script',
            'script_generated': True,
            'generated_script': script,
            'execution_result': execution_result
        }
    
    def handle_user_input(self, user_input: str) -> str:
        """
        Handle user input and return a response.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            Formatted response string for display
        """
        try:
            result = self.process_request(user_input)
            
            if result['type'] == 'plugin_result':
                return f"Plugin executed successfully: {result['plugin_result']}"
            elif result['type'] == 'fusion_script' and result['script_generated']:
                execution_result = result['execution_result']
                if execution_result['success']:
                    response = "Script executed successfully.\n"
                    if execution_result['output']:
                        response += f"Output: {execution_result['output']}"
                    return response
                else:
                    return f"Script execution failed: {execution_result['error']}\nError details: {execution_result['error_output']}"
            else:
                return "Could not process the request."
        
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            return error_msg
    
    def run_interactive_mode(self):
        """Run the MCP in interactive mode (command line interface)."""
        print("FusionMCP Interactive Mode")
        print("Type 'quit' or 'exit' to exit")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\nFusionMCP> ")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Exiting FusionMCP...")
                    break
                
                if user_input.strip() == "":
                    continue
                
                response = self.handle_user_input(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\nExiting FusionMCP...")
                break
            except EOFError:
                print("\nExiting FusionMCP...")
                break
    
    def run_dialog_interface(self):
        """Run the MCP with a dialog box interface (for Fusion 360 integration)."""
        # This would integrate with Fusion 360's dialog system
        # For now, we'll simulate it
        print("FusionMCP Dialog Interface")
        print("(This would appear as a dialog in Fusion 360)")
        print("Enter your request in the dialog box.")
        
        # In an actual Fusion 360 add-in, this would create a dialog
        # For this example, we'll just call interactive mode
        self.run_interactive_mode()


# Fusion 360 Add-in Entry Points
# These would be called by Fusion 360 when the add-in is loaded
class FusionMCPCommand:
    """Command class for Fusion 360 add-in."""
    
    def __init__(self):
        self.command_name = "FusionMCP"
        self.command_description = "Multi-Modal Control Plane for Fusion 360"
        self.mcp = FusionMCP()
    
    def start(self, app):
        """Start the MCP with Fusion 360 application."""
        self.mcp.set_fusion_app(app)
        print("FusionMCP started")
        # In a real add-in, this would open the dialog
        self.mcp.run_dialog_interface()
    
    def stop(self):
        """Stop the MCP."""
        print("FusionMCP stopped")


# Main entry point when running as standalone script
def main():
    """Main function to run FusionMCP."""
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    
    mcp = FusionMCP(config_path)
    
    # Check if running in Fusion 360 environment
    fusion_env = False
    try:
        import adsk.core
        import adsk.fusion
        fusion_env = True
    except ImportError:
        pass  # Not in Fusion 360 environment
    
    if fusion_env:
        # Running in Fusion 360 - use dialog interface
        print("FusionMCP detected Fusion 360 environment")
        mcp.run_dialog_interface()
    else:
        # Running standalone - use interactive mode
        print("FusionMCP running in standalone mode")
        mcp.run_interactive_mode()


if __name__ == "__main__":
    main()