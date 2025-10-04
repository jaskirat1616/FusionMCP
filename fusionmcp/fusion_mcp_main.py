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
from .fusion_command_executor import FusionCommandExecutor
from .plugin_manager import PluginManager


class FusionMCP:
    """Main FusionMCP orchestrator class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.context_manager = ContextManager()
        self.ai_interface = AIInterface(config_path)
        # Use standard command executor by default
        self.command_executor = CommandExecutor()
        self.plugin_manager = PluginManager(config_path)

        # Store Fusion 360 application reference if available
        self.fusion_app = None

        # Check if running in Fusion 360 environment
        self.is_fusion_environment = False
        try:
            import adsk.core
            import adsk.fusion
            self.is_fusion_environment = True
        except ImportError:
            pass

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
        """Set the Fusion 360 application object and update command executor."""
        self.fusion_app = app
        # Use Fusion-specific executor when in Fusion 360 environment
        try:
            import adsk.core
            import adsk.fusion
            from .fusion_command_executor import FusionCommandExecutor
            self.command_executor = FusionCommandExecutor()
        except ImportError:
            # Not in Fusion 360 environment, keep standard executor
            pass
    
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
            error_output = execution_result.get('error_output', execution_result.get('error', 'Unknown error'))
            fixed_script = self.ai_interface.validate_and_fix_script(script, error_output)
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
        # Check if running in standalone mode (not in Fusion 360)
        if not self.is_fusion_environment and not self.fusion_app:
            return self._handle_standalone_mode(user_input)

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

    def _handle_standalone_mode(self, user_input: str) -> str:
        """Handle requests in standalone mode (demo/testing mode)."""
        user_input_lower = user_input.lower().strip()

        # Handle special commands
        if user_input_lower == 'plugins':
            plugins = self.plugin_manager.list_plugins()
            return f"✓ Available plugins:\n  " + "\n  ".join(f"• {p}" for p in plugins)

        if user_input_lower.startswith('material '):
            material_name = user_input[9:].strip()
            result = self.plugin_manager.execute_plugin('material_database', {'material': material_name})
            if result.get('success'):
                props = result['properties']
                return f"""✓ Material: {result['material']}
  Density: {props['density']} g/cm³
  Tensile Strength: {props['tensile_strength']} MPa
  Yield Strength: {props['yield_strength']} MPa
  Young's Modulus: {props['youngs_modulus']} GPa
  Poisson's Ratio: {props['poissons_ratio']}"""
            else:
                return f"✗ {result.get('error', 'Material not found')}"

        # Try plugin execution for other inputs
        plugin_result = self.plugin_manager.execute_plugin_if_appropriate(user_input)
        if plugin_result and plugin_result.get('success'):
            return f"✓ Plugin executed: {plugin_result}"

        # Provide helpful information for standalone mode
        return f"""
FusionMCP is running in STANDALONE MODE (demo mode).

This mode is for testing the system without Fusion 360.

Your input: "{user_input}"

To use FusionMCP with Fusion 360:
  1. Install the add-in (see fusion360_addin/INSTALL.md)
  2. Start Fusion 360
  3. Use the MCP Tab > Start MCP button

Available commands in standalone mode:
  - 'plugins' - List available plugins
  - 'material <name>' - Query material database (e.g., 'material steel')
  - 'quit' or 'exit' - Exit the program

Try: 'material aluminum' to test the material database plugin
"""
    
    def run_interactive_mode(self):
        """Run the MCP in interactive mode (command line interface)."""
        print("=" * 60)
        print("FusionMCP Interactive Mode")
        if not self.is_fusion_environment and not self.fusion_app:
            print("Running in STANDALONE MODE (demo/testing)")
            print()
            print("Available commands:")
            print("  • plugins        - List available plugins")
            print("  • material <name> - Query material database")
            print("  • quit/exit      - Exit the program")
            print()
            print("Note: Full Fusion 360 integration requires the add-in.")
        else:
            print("Running with Fusion 360 integration")
        print("Type 'quit' or 'exit' to exit")
        print("=" * 60)
        
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