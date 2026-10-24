# FusionMCP Fusion add-in

Generate Python with your configured AI provider, review the complete script,
then explicitly confirm execution. See [installation instructions](INSTALL.md).

## Verified environment

An end user successfully generated and executed a script using:

- Autodesk Fusion Personal **2706.1.14 x86_64**
- Windows
- LM Studio's local OpenAI-compatible API
- Fusion's embedded Python 3.14

This is a compatibility report for that environment, not a guarantee for every
generated script, provider, document type, or operating system. Mac and other
providers have not been manually verified as part of this change.

## Usage

1. Keep your configured AI service running.
2. Open a design. Select **Utilities > Scripts and Add-Ins**, select
   **FusionMCP**, and click **Run**. If the toolbar differs, search for
   **Scripts and Add-Ins** using **S**.
3. Enter a request, then click **Generate preview**. No code is executed here.
4. Review the complete Python shown in the preview.
5. **Execute reviewed script** is enabled only after successful generation and
   validation. It is disabled again if the request changes or generation fails.
6. Type `EXECUTE` in the separate confirmation prompt to execute the reviewed
   script once. There is no automatic execution retry.

The **FusionMCP** toolbar command reopens the dialog. Restart Fusion after
updating Python modules, because imported package modules can remain cached.

## Behavior and limitations

- The add-in calls the configured AI interface directly instead of
  `FusionMCP.process_request`, which executes scripts internally. This avoids
  executing during preview and executing the same script a second time.
- Fusion-style `run(context)` scripts are invoked once after their definitions;
  top-level scripts remain supported.
- Generation guidance uses the official `adsk.core` and `adsk.fusion` API,
  centimeter-based numeric lengths, and Part/Assembly/Hybrid design intent.
  Part Designs use the existing root component rather than adding a child.
  Guidance is not a guarantee that a model will produce correct API calls.
- Leading reasoning output, including a standalone closing `</think>` from
  reasoning templates that omit the opening tag, is removed before validation.
  One complete Python Markdown block can be extracted from surrounding prose.
  Ambiguous/incomplete blocks, empty answers, and invalid Python are rejected.
- Missing imports such as an invented `f3dapi` wrapper are rejected at preview.
  This check does not validate every API method or operation.
- The add-in entry point does not use the orchestrator's plugins or persistent
  conversation storage. Standalone orchestrator behavior is unchanged.

**Python runs with your user permissions. Validation is not a security sandbox.**
Inspect the script, use a disposable design first, and verify geometry and units.
A local model connection does not disable Autodesk Fusion's own cloud services.

## Regression tests

Install `requests` and `PyYAML` into your test interpreter, then from the
repository root run:

```text
python -B -m unittest -v test_local_install
```

Tests mock the native Fusion UI and do not create CAD geometry. Live model
requests are separate manual checks, not part of this offline suite.
