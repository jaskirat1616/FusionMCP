"""FusionMCP add-in: generate, review, then explicitly execute."""

import html
import os
import sys
import traceback

import adsk.core
import adsk.fusion


ADDIN_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = (
    ADDIN_DIR if os.path.isdir(os.path.join(ADDIN_DIR, "fusionmcp"))
    else os.path.dirname(ADDIN_DIR)
)
for path in (PACKAGE_DIR, os.path.join(PACKAGE_DIR, "_vendor")):
    if path not in sys.path:
        sys.path.insert(0, path)

COMMAND_ID = "FusionMCPReview"
_handlers = []


def run(context):
    ui = adsk.core.Application.get().userInterface
    try:
        from fusionmcp.ai_interface import AIInterface

        config_path = os.path.join(ADDIN_DIR, "config.yaml")
        if not os.path.isfile(config_path):
            raise FileNotFoundError("Place config.yaml beside FusionMCP.py.")
        ai = AIInterface(config_path)
        definition = ui.commandDefinitions.itemById(COMMAND_ID)
        if definition:
            definition.deleteMe()
        definition = ui.commandDefinitions.addButtonDefinition(
            COMMAND_ID, "FusionMCP",
            "Generate with your configured provider, review Python, then confirm execution."
        )
        handler = CommandCreatedHandler(ai)
        definition.commandCreated.add(handler)
        _handlers.append(handler)
        panel = ui.workspaces.itemById("FusionSolidEnvironment").toolbarPanels.itemById(
            "SolidScriptsAddinsPanel"
        )
        if panel is None:
            raise RuntimeError("Fusion's Scripts and Add-Ins toolbar panel was not found.")
        control = panel.controls.itemById(COMMAND_ID)
        if control is None:
            control = panel.controls.addCommand(definition)
        control.isPromoted = True
        definition.execute()
    except Exception:
        ui.messageBox("FusionMCP could not start:\n" + traceback.format_exc())


def stop(context):
    ui = adsk.core.Application.get().userInterface
    try:
        workspace = ui.workspaces.itemById("FusionSolidEnvironment")
        if workspace:
            panel = workspace.toolbarPanels.itemById("SolidScriptsAddinsPanel")
            if panel:
                control = panel.controls.itemById(COMMAND_ID)
                if control:
                    control.deleteMe()
        definition = ui.commandDefinitions.itemById(COMMAND_ID)
        if definition:
            definition.deleteMe()
        _handlers.clear()
    except Exception:
        ui.messageBox("FusionMCP could not stop:\n" + traceback.format_exc())


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, ai):
        super().__init__()
        self.ai = ai

    def notify(self, args):
        ui = adsk.core.Application.get().userInterface
        try:
            command = args.command
            command.okButtonText = "Execute reviewed script"
            inputs = command.commandInputs
            inputs.addTextBoxCommandInput(
                "request", "Request",
                "Create a new component containing a 10 mm cube.", 4, False
            )
            inputs.addBoolValueInput("generate", "Generate preview", False, "", False)
            inputs.addTextBoxCommandInput(
                "preview", "Python preview",
                "Generate a preview first. Nothing is executed during generation.",
                18, True
            )
            state = {"script": None}
            changed = InputChangedHandler(self.ai, state)
            execute = ExecuteHandler(state)
            validate = ValidateInputsHandler(state)
            command.inputChanged.add(changed)
            command.execute.add(execute)
            command.validateInputs.add(validate)
            _handlers.extend((changed, execute, validate))
        except Exception:
            ui.messageBox("FusionMCP dialog failed:\n" + traceback.format_exc())


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self, ai, state):
        super().__init__()
        self.ai = ai
        self.state = state

    def notify(self, args):
        ui = adsk.core.Application.get().userInterface
        try:
            inputs = args.inputs
            preview = inputs.itemById("preview")
            if args.input.id == "request":
                self.state["script"] = None
                preview.formattedText = "Request changed. Generate a new preview."
                return
            if args.input.id != "generate" or not args.input.value:
                return
            args.input.value = False
            self.state["script"] = None
            preview.formattedText = "Generating with the configured AI provider..."
            request = inputs.itemById("request").text.strip()
            if not request:
                raise ValueError("Enter a design request before generating.")
            script = self.ai.generate_fusion_script(request)
            compile(script, "<FusionMCP preview>", "exec")
            from fusionmcp.fusion_command_executor import FusionScriptValidator

            validation = FusionScriptValidator().validate_script(script)
            if not validation["is_safe"]:
                preview.formattedText = html.escape("\n".join(validation["errors"]))
                ui.messageBox(
                    "\n".join(validation["errors"]),
                    "FusionMCP - Generated script rejected"
                )
                return
            preview.formattedText = "<pre>" + html.escape(script) + "</pre>"
            self.state["script"] = script
        except Exception:
            self.state["script"] = None
            args.inputs.itemById("preview").formattedText = (
                "Generation failed. See the error dialog, then generate again."
            )
            ui.messageBox("FusionMCP generation failed:\n" + traceback.format_exc())


class ValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self, state):
        super().__init__()
        self.state = state

    def notify(self, args):
        args.areInputsValid = bool(self.state["script"])


class ExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, state):
        super().__init__()
        self.state = state

    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface
        try:
            from fusionmcp.fusion_command_executor import FusionCommandExecutor

            script = self.state["script"]
            if not script:
                ui.messageBox(
                    "Click Generate preview first, then review the Python before "
                    "clicking Execute reviewed script.",
                    "FusionMCP - Preview required"
                )
                return
            executor = FusionCommandExecutor()
            validation = executor.validator.validate_script(script)
            if not validation["is_safe"]:
                raise ValueError("\n".join(validation["errors"]))
            answer, cancelled = ui.inputBox(
                "Type EXECUTE to run the Python you just reviewed.\n\n"
                "Generated code has your user permissions. Validation is NOT a sandbox.\n"
                "Use a disposable design and do not execute code you do not understand.",
                "FusionMCP - Confirm execution",
                ""
            )
            if cancelled or answer != "EXECUTE":
                return
            self.state["script"] = None
            result = executor.execute_script(script, app)
            if not result["success"]:
                raise RuntimeError(
                    result.get("error_output") or result.get("error") or str(result)
                )
            ui.messageBox("Script executed once.\n" + result.get("output", ""))
        except Exception:
            ui.messageBox("FusionMCP execution failed:\n" + traceback.format_exc())
