"""Offline regression tests for FusionMCP's review-first add-in."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "_vendor"))
sys.path.insert(0, str(ROOT))

# Fusion's native UI is only available inside Fusion; mock that boundary.
adsk = types.ModuleType("adsk")
core = types.ModuleType("adsk.core")
fusion = types.ModuleType("adsk.fusion")
for name in (
    "CommandCreatedEventHandler", "InputChangedEventHandler",
    "CommandEventHandler", "ValidateInputsEventHandler"
):
    setattr(core, name, type(name, (), {}))
ui = MagicMock()
core.Application = MagicMock()
core.Application.get.return_value.userInterface = ui
adsk.core = core
adsk.fusion = fusion
sys.modules.update({"adsk": adsk, "adsk.core": core, "adsk.fusion": fusion})

spec = importlib.util.spec_from_file_location(
    "local_addin", ROOT / "fusion360_addin" / "FusionMCP.py"
)
addin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(addin)

from fusionmcp.ai_interface import AIInterface, LMStudioProvider
from fusionmcp.fusion_command_executor import FusionCommandExecutor, FusionScriptValidator


class LocalInstallTests(unittest.TestCase):
    def setUp(self):
        ui.reset_mock()

    def changed_args(self, changed_id="generate", request="Make a cube"):
        inputs = {
            "request": types.SimpleNamespace(text=request),
            "generate": types.SimpleNamespace(id="generate", value=True),
            "preview": types.SimpleNamespace(formattedText=""),
        }
        return types.SimpleNamespace(
            input=inputs.get(changed_id, types.SimpleNamespace(id=changed_id)),
            inputs=types.SimpleNamespace(itemById=inputs.get)
        )

    def test_preview_does_not_execute(self):
        state = {"script": None}
        ai = MagicMock()
        ai.generate_fusion_script.return_value = "print('preview only')"
        args = self.changed_args()
        with patch.object(FusionCommandExecutor, "execute_script") as execute:
            addin.InputChangedHandler(ai, state).notify(args)
        execute.assert_not_called()
        self.assertEqual(state["script"], "print('preview only')")
        self.assertIn("preview only", args.inputs.itemById("preview").formattedText)

    def test_unsupported_imports_rejected_before_execution(self):
        for script in (
            "import f3dapi", "from f3dapi import Application",
            "import f3dapi.core as core", "import cadquery",
            "from . import helper",
        ):
            with self.subTest(script=script):
                state = {"script": None}
                ai = MagicMock()
                ai.generate_fusion_script.return_value = script
                args = self.changed_args()
                with patch.object(FusionCommandExecutor, "execute_script") as execute:
                    addin.InputChangedHandler(ai, state).notify(args)
                execute.assert_not_called()
                self.assertIsNone(state["script"])
                self.assertIn("Unsupported import", args.inputs.itemById("preview").formattedText)

    def test_official_api_and_stdlib_imports_remain_valid(self):
        result = FusionScriptValidator().validate_script(
            "import adsk.core\nimport adsk.fusion\nimport math\n"
            "from collections import namedtuple\n"
        )
        self.assertTrue(result["is_safe"], result)

    def test_generation_prompt_requires_official_api_and_units(self):
        ai = AIInterface.__new__(AIInterface)
        ai.provider = MagicMock()
        ai.provider.generate_response.return_value = "print('test')"
        ai.generate_fusion_script("Make a cube")
        prompt = ai.provider.generate_response.call_args.args[0]
        for required in ("adsk.core", "adsk.fusion", "Do NOT import f3dapi", "10 mm = 1 cm"):
            self.assertIn(required, prompt)

    def test_prompt_component_selection_supports_part_and_assembly(self):
        ai = AIInterface.__new__(AIInterface)
        ai.provider = MagicMock()
        ai.provider.generate_response.return_value = "print('test')"
        ai.generate_fusion_script("Create a new component containing a cube")
        prompt = ai.provider.generate_response.call_args.args[0]
        start = prompt.index("        if design.designIntent ==")
        end = prompt.index("        In a Part Design", start)
        import textwrap
        selection = textwrap.dedent(prompt[start:end])
        intents = types.SimpleNamespace(PartDesignIntentType=0)
        api = types.SimpleNamespace(
            fusion=types.SimpleNamespace(DesignIntentTypes=intents),
            core=types.SimpleNamespace(Matrix3D=MagicMock())
        )
        for intent in (0, 1, 2):
            with self.subTest(intent=intent):
                root = MagicMock()
                scope = {
                    "adsk": api, "root": root,
                    "design": types.SimpleNamespace(designIntent=intent)
                }
                exec(selection, scope)
                if intent == 0:
                    self.assertIs(scope["component"], root)
                    root.occurrences.addNewComponent.assert_not_called()
                else:
                    root.occurrences.addNewComponent.assert_called_once()
                    self.assertIs(
                        scope["component"],
                        root.occurrences.addNewComponent.return_value.component
                    )
                self.assertEqual(scope["design"].designIntent, intent)

    def test_execute_is_disabled_until_preview_ready(self):
        state = {"script": None}
        handler = addin.ValidateInputsHandler(state)
        args = types.SimpleNamespace(areInputsValid=True)
        handler.notify(args)
        self.assertFalse(args.areInputsValid)
        ai = MagicMock()
        ai.generate_fusion_script.return_value = "print('ready')"
        addin.InputChangedHandler(ai, state).notify(self.changed_args())
        handler.notify(args)
        self.assertTrue(args.areInputsValid)
        changed = self.changed_args("request")
        changed.input.id = "request"
        addin.InputChangedHandler(ai, state).notify(changed)
        handler.notify(args)
        self.assertFalse(args.areInputsValid)

    def test_validation_handler_is_wired_to_command(self):
        command = MagicMock()
        addin.CommandCreatedHandler(MagicMock()).notify(
            types.SimpleNamespace(command=command)
        )
        command.validateInputs.add.assert_called_once()
        handler = command.validateInputs.add.call_args.args[0]
        self.assertIsInstance(handler, addin.ValidateInputsHandler)
        self.assertIn(handler, addin._handlers)

    def test_missing_preview_shows_instructions_without_traceback(self):
        with patch.object(FusionCommandExecutor, "execute_script") as execute:
            addin.ExecuteHandler({"script": None}).notify(None)
        execute.assert_not_called()
        message = ui.messageBox.call_args.args[0]
        self.assertIn("Click Generate preview first", message)
        self.assertNotIn("Traceback", message)

    def test_request_change_invalidates_preview(self):
        state = {"script": "print('old')"}
        args = self.changed_args("request")
        args.input.id = "request"
        addin.InputChangedHandler(MagicMock(), state).notify(args)
        self.assertIsNone(state["script"])

    def test_generation_failure_clears_old_script(self):
        for output in ("invalid python!", None):
            with self.subTest(output=output):
                state = {"script": "print('old')"}
                ai = MagicMock()
                ai.generate_fusion_script.return_value = output
                addin.InputChangedHandler(ai, state).notify(self.changed_args())
                self.assertIsNone(state["script"])
                ui.messageBox.assert_called()
                args = types.SimpleNamespace(areInputsValid=True)
                addin.ValidateInputsHandler(state).notify(args)
                self.assertFalse(args.areInputsValid)

    def test_confirmation_must_be_explicit(self):
        for answer in (("", False), ("EXECUTE", True), ("execute", False)):
            with self.subTest(answer=answer):
                ui.inputBox.return_value = answer
                with patch.object(FusionCommandExecutor, "execute_script") as execute:
                    addin.ExecuteHandler({"script": "print('test')"}).notify(None)
                execute.assert_not_called()

    def test_execution_occurs_once(self):
        ui.inputBox.return_value = ("EXECUTE", False)
        state = {"script": "print('test')"}
        with patch.object(
            FusionCommandExecutor, "execute_script",
            return_value={"success": True, "output": ""}
        ) as execute:
            handler = addin.ExecuteHandler(state)
            handler.notify(None)
            handler.notify(None)
        execute.assert_called_once()
        self.assertIsNone(state["script"])

    def test_missing_or_rejected_script_never_executes(self):
        for script in (None, "import subprocess"):
            with self.subTest(script=script):
                with patch.object(FusionCommandExecutor, "execute_script") as execute:
                    addin.ExecuteHandler({"script": script}).notify(None)
                execute.assert_not_called()

    def test_fusion_entry_point_runs_once(self):
        result = FusionCommandExecutor().execute_script(
            "def run(context):\n    print('entry called')\n"
            "if __name__ == '__main__':\n    run(None)\n"
        )
        self.assertTrue(result["success"], result)
        self.assertEqual(result["output"], "entry called\n")

    def test_top_level_script_preserved(self):
        result = FusionCommandExecutor().execute_script("print('top level')")
        self.assertTrue(result["success"], result)
        self.assertEqual(result["output"], "top level\n")

    def test_provider_rejects_empty_or_truncated_responses(self):
        for payload in (
            {"choices": []},
            {"choices": [{"message": {"content": ""}}]},
            {"choices": [{"finish_reason": "length", "message": {"content": "pass"}}]},
        ):
            with self.subTest(payload=payload), patch(
                "fusionmcp.ai_interface.requests.post"
            ) as post:
                post.return_value.json.return_value = payload
                with self.assertRaises(ValueError):
                    LMStudioProvider().generate_response("test")

    def test_provider_connection_failure_is_explicit(self):
        import requests
        with patch(
            "fusionmcp.ai_interface.requests.post",
            side_effect=requests.exceptions.ConnectionError("offline")
        ):
            with self.assertRaisesRegex(RuntimeError, "Could not connect"):
                LMStudioProvider().generate_response("test")

    def test_reasoning_is_removed_before_preview(self):
        ai = AIInterface.__new__(AIInterface)
        script = ai._clean_script(
            "<think>\nReasoning with non-Python syntax.\n</think>\n"
            "```python\nprint('LOCAL_LLM_CONNECTED')\n```"
        )
        self.assertEqual(script, "print('LOCAL_LLM_CONNECTED')")
        compile(script, "<test>", "exec")

    def test_incomplete_reasoning_is_rejected(self):
        ai = AIInterface.__new__(AIInterface)
        for script in ("<think>unfinished", "<think>reasoning</think>"):
            with self.subTest(script=script), self.assertRaises(ValueError):
                ai._clean_script(script)

    def test_reasoning_response_shapes(self):
        ai = AIInterface.__new__(AIInterface)
        expected = "print('ready')"
        for response in (
            "Unclosed-template reasoning, not Python.\n</think>\n" + expected,
            "<think>Reasoning</think>\n" + expected,
            "<think>Reasoning</think>\nHere is the script:\n```python\n"
            + expected + "\n```\nExplanation: Done.",
            "```python\n" + expected + "\n```\nHere is why this works.",
            "Reasoning\r\n </think> \r\n```py\r\n" + expected + "\r\n```",
            expected,
        ):
            with self.subTest(response=response):
                self.assertEqual(ai._clean_script(response), expected)

    def test_ambiguous_or_invalid_responses_are_rejected(self):
        ai = AIInterface.__new__(AIInterface)
        for response in (
            "print('reasoning code')\n</think>\nHere is my explanation.",
            "```python\nprint('incomplete')",
            "```python\npass\n```\n```python\npass\n```",
            "```javascript\nconsole.log('no')\n```",
            "<think>Reasoning</think>\n</think>\npass",
            "# Comments only",
            "print('valid prefix')\nExplanation: extra prose",
            "",
        ):
            with self.subTest(response=response), self.assertRaises(ValueError):
                ai._clean_script(response)

    def test_cleaner_preserves_comments_strings_and_all_statements(self):
        ai = AIInterface.__new__(AIInterface)
        script = (
            "print('</think>')\n"
            "# Note: this comment must not truncate the script\n"
            "print('second statement')"
        )
        self.assertEqual(ai._clean_script(script), script)


if __name__ == "__main__":
    unittest.main()
