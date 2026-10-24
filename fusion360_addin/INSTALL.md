# Installing the FusionMCP add-in

## File layout

Install a self-contained folder named `FusionMCP` with this structure:

```text
FusionMCP\
  FusionMCP.py
  FusionMCP.manifest
  config.yaml
  fusionmcp\
    __init__.py
    ...
  _vendor\
    requests\
    yaml\
    ...
```

Copy `FusionMCP.py`, `FusionMCP.manifest`, and `config.yaml` from this
`fusion360_addin` directory. Copy the repository's `fusionmcp` package alongside
them. Copying only `fusion360_addin` is not sufficient.

The `FusionMCP.manifest` filename is significant: it matches `FusionMCP.py`.
The older `manifest.json` is not a replacement for Fusion's add-in manifest.

For a source checkout, you may instead register `fusion360_addin` directly:
the entry point also finds `fusionmcp` and `_vendor` in its parent directory.

## Dependencies

Fusion embeds its own Python. Installing packages into an unrelated system
Python does not make them available inside Fusion.

For LM Studio and Ollama, only `requests` and `PyYAML` and their dependencies
are needed. Use an available pip-enabled interpreter compatible with Fusion's
Python version and operating system to install them into the private `_vendor`
directory, for example:

```text
python -m pip install --only-binary=:all: --target "<FusionMCP folder>\_vendor" requests PyYAML
```

Use Fusion's actual Python version, not an assumed version. The verified Windows
build used Python 3.14; PyYAML contains version/platform-specific native code.
If Fusion's embedded Python has no pip, do not modify its global installation:
use a compatible external interpreter or a pip bootstrap with that interpreter.
Install `google-generativeai` there as well only when selecting Gemini.
The complete optional provider dependencies remain in `requirements.txt`.

## Configuration

Edit `config.yaml` beside the installed `FusionMCP.py`. Preserve your chosen
provider and credentials; never commit private configuration.

For LM Studio, start the local server, load a model, and set its exact model ID:

```yaml
ai_provider: "lm_studio"
lm_studio_model: "replace-with-your-loaded-model-id"
lm_studio_url: "http://127.0.0.1:1234/v1/chat/completions"
plugins: []
```

The add-in uses the configured provider; it does not force LM Studio or select a
particular model. Existing Ollama/OpenAI/Gemini configuration remains supported
but was not manually verified in the reported Windows compatibility test.

## Register and run

On the verified Windows installation the add-in directory was:

```text
%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\FusionMCP
```

Fusion versions and custom API preferences can use other directories. The
reliable way to register is to open **Scripts and Add-Ins**, use the add/import
control, and select the installed `FusionMCP` folder.

Open a design, select the **Utilities** tab (not **Solid**), and find
**Scripts and Add-Ins**. Alternatively press **S** and search for that command.
Select **FusionMCP** and run it. Automatic startup is disabled in the manifest.

See [usage and compatibility notes](README.md) for preview and confirmation.
Restart Fusion completely after updating package files to clear module caches.

## Troubleshooting

- **No add-in entry:** check the matching `.py`/`.manifest` filenames and the
  registered folder. Restart Fusion after installation.
- **Missing requests or yaml:** check `_vendor` layout and Python compatibility.
- **Connection failure:** check your model server and the configured endpoint.
- **Unsupported import (f3dapi):** regenerate using the official `adsk` API;
  do not try to install an invented wrapper.
- **Part Design component error:** generate a new preview that creates bodies
  in the existing root component, not another component. Do not convert a
  document merely to work around generated code.
- **Invalid model output:** regenerate. The parser rejects incomplete Python
  and reasoning/prose it cannot unambiguously separate from the script.
