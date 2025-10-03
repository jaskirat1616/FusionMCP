"""
Example workflow for FusionMCP

This module demonstrates a complete workflow:
- User prompt → AI generates Python script → MCP executes script in Fusion 360 → logs output
"""

from fusionmcp.context_manager import ContextManager
from fusionmcp.ai_interface import AIInterface
from fusionmcp.command_executor import CommandExecutor
from fusionmcp.plugin_manager import PluginManager
from fusionmcp.fusion_mcp_main import FusionMCP
import os


def example_workflow():
    """Demonstrate a complete FusionMCP workflow."""
    print("=== FusionMCP Example Workflow ===\n")
    
    # Step 1: Initialize the MCP system
    print("1. Initializing FusionMCP system...")
    mcp = FusionMCP()
    print("   ✓ System initialized\n")
    
    # Step 2: User provides a request
    user_request = "Create a cube with dimensions 10mm x 10mm x 10mm at the origin"
    print(f"2. User request: '{user_request}'\n")
    
    # Step 3: Process the request through the MCP pipeline
    print("3. Processing request through MCP pipeline...")
    result = mcp.process_request(user_request)
    print("   ✓ Request processed\n")
    
    # Step 4: Display the generated script
    if result['type'] == 'fusion_script' and result['script_generated']:
        print("4. Generated Fusion 360 script:")
        print("-" * 40)
        print(result['generated_script'])
        print("-" * 40)
        print("   ✓ Script generated\n")
        
        # Step 5: Show execution results
        execution_result = result['execution_result']
        print("5. Script execution results:")
        print(f"   Success: {execution_result['success']}")
        if execution_result['output']:
            print(f"   Output: {execution_result['output']}")
        if execution_result['error']:
            print(f"   Error: {execution_result['error']}")
        print("   ✓ Execution completed\n")
    
    # Step 6: Show context management
    print("6. Context management:")
    recent_context = mcp.context_manager.get_recent_context(1)
    print(f"   Recent interactions stored: {len(recent_context)}")
    print("   ✓ Context preserved\n")
    
    # Step 7: Demonstrate plugin usage
    print("7. Plugin demonstration:")
    material_result = mcp.plugin_manager.execute_plugin(
        "material_database", 
        {"material": "aluminum"}
    )
    print(f"   Material properties for aluminum: {material_result}")
    print("   ✓ Plugin executed\n")
    
    print("=== Workflow completed ===")


def advanced_example():
    """Demonstrate a more complex workflow with error handling."""
    print("\n=== Advanced Example: Error Handling ===\n")
    
    # Create a FusionMCP instance
    mcp = FusionMCP()
    
    # User request that might generate an invalid script
    user_request = "Create a complex assembly with 10 parts that interlock"
    print(f"Request: '{user_request}'")
    
    # Process the request
    result = mcp.process_request(user_request)
    
    if result['type'] == 'fusion_script':
        print("Generated script:")
        print(result['generated_script'])
        
        execution_result = result['execution_result']
        print(f"\nExecution success: {execution_result['success']}")
        
        if not execution_result['success']:
            print("Script failed to execute, AI attempted to fix it.")
        else:
            print("Script executed successfully!")
    
    print("\n=== Advanced example completed ===")


if __name__ == "__main__":
    # Run the example workflow
    example_workflow()
    
    # Run the advanced example
    advanced_example()
    
    print("\nAll examples completed successfully!")