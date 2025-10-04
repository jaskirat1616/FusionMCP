# Fusion 360 Add-in for FusionMCP
# Provides real-time integration with Fusion 360

import adsk.core
import adsk.fusion
import traceback
import os
import sys

# Add user's Python site-packages for dependencies FIRST (requests, yaml, etc.)
# Try multiple possible Python 3.9 locations
home_dir = os.path.expanduser('~')
possible_paths = [
    os.path.join(home_dir, 'Library', 'Python', '3.9', 'lib', 'python', 'site-packages'),
    '/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/site-packages',
    '/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages'
]

for path in possible_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# Add the parent directory to the path so we can import fusionmcp package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from fusionmcp.fusion_mcp_main import FusionMCP
from fusionmcp.fusion_command_executor import FusionCommandExecutor


def run(context):
    """The run function for the add-in, called when the add-in is started."""
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Find the config file - check multiple locations
        addin_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(addin_dir)

        config_locations = [
            os.path.join(addin_dir, 'config.yaml'),
            os.path.join(parent_dir, 'config.yaml'),
            os.path.expanduser('~/FusionMCP/config.yaml')
        ]

        config_path = 'config.yaml'  # Default fallback
        for path in config_locations:
            if os.path.exists(path):
                config_path = path
                break

        # Create the FusionMCP instance with proper config path
        mcp = FusionMCP(config_path)

        # Set the Fusion 360 application in the MCP
        mcp.set_fusion_app(app)

        # Create a command for the add-in
        cmd_def = ui.commandDefinitions.itemById('FusionMCP.Start')
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                'FusionMCP.Start',
                'Start MCP',
                'Launch the Multi-Modal Control Plane for Fusion 360',
                './resources/mcp_icon.png'
            )

        # Connect to the command created event
        on_execute = FusionMCPCommandCreatedEventHandler(mcp)
        cmd_def.commandCreated.add(on_execute)

        # Execute the command
        cmd_def.execute()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    """The stop function for the add-in, called when the add-in is stopped."""
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Clean up the command definition
        cmd_def = ui.commandDefinitions.itemById('FusionMCP.Start')
        if cmd_def:
            cmd_def.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class FusionMCPCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    """Event handler for when the MCP command is created."""

    def __init__(self, mcp):
        super().__init__()
        self.mcp = mcp

    def notify(self, args):
        try:
            # Create the command
            cmd = args.command
            cmd.isOKButtonVisible = True
            cmd.isCancelButtonVisible = True

            # Connect to the execute event
            on_execute = FusionMCPCommandExecuteHandler(self.mcp)
            cmd.execute.add(on_execute)

            # Connect to the input changed event
            on_input_changed = FusionMCPCommandInputChangedHandler(self.mcp)
            cmd.inputChanged.add(on_input_changed)

            # Connect to the destroy event
            on_destroy = FusionMCPCommandDestroyHandler()
            cmd.destroy.add(on_destroy)

            # Add inputs to the command dialog
            inputs = cmd.commandInputs
            input_text = inputs.addTextBoxCommandInput('inputText', 'Enter your request:', 'Create a cube with dimensions 10mm x 10mm x 10mm', 5, True)
            execute_button = inputs.addBoolValueInput('executeButton', 'Execute', False, '', True)

        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class FusionMCPCommandExecuteHandler(adsk.core.CommandEventHandler):
    """Event handler for when the MCP command is executed."""

    def __init__(self, mcp):
        super().__init__()
        self.mcp = mcp

    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            cmd = args.firingEvent.sender

            # Get the input values
            input_text = cmd.commandInputs.itemById('inputText').text
            should_execute = cmd.commandInputs.itemById('executeButton').value

            if input_text.strip() == '':
                ui.messageBox('Please enter a request.')
                return

            # Process the request through FusionMCP
            ui.messageBox('Processing request: {}'.format(input_text))

            # Use the MCP to process the request
            result = self.mcp.process_request(input_text)

            if result['type'] == 'fusion_script':
                script = result['generated_script']

                if should_execute:
                    # Execute the script in Fusion 360
                    executor = FusionCommandExecutor()
                    execution_result = executor.execute_script(script, app)

                    if execution_result['success']:
                        ui.messageBox('Script executed successfully!\nOutput: {}'.format(execution_result['output']))
                    else:
                        ui.messageBox('Script execution failed!\nError: {}'.format(execution_result['error_output']))
                else:
                    # Just show the generated script
                    ui.messageBox('Generated script:\n{}'.format(script[:500] + '...' if len(script) > 500 else script))
            else:
                ui.messageBox('Could not process the request.')

        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class FusionMCPCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    """Event handler for when command inputs change."""

    def __init__(self, mcp):
        super().__init__()
        self.mcp = mcp

    def notify(self, args):
        try:
            changed_input = args.input
            # Handle input changes if needed
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class FusionMCPCommandDestroyHandler(adsk.core.CommandEventHandler):
    """Event handler for when the command is destroyed."""

    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            # Clean up if needed
            pass
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
