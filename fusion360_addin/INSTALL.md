# Installation Guide for FusionMCP Add-in

## Prerequisites
- Autodesk Fusion 360
- Python 3.8+ with required packages (PyYAML, requests, google-generativeai, openai)
- An AI backend: Ollama (recommended), LM Studio, OpenAI, or Google Gemini

## Installation Steps

### Method 1: Install from Project Directory (Development)

1. **Locate Fusion 360 Add-ins Directory**:

   **Windows**:
   ```
   %APPDATA%\Autodesk\Autodesk Fusion 360\API\Addins
   ```

   **Mac**:
   ```
   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Addins
   ```

2. **Create Symbolic Link or Copy Files**:

   **Option A - Symbolic Link (Recommended for development)**:
   ```bash
   # Windows (run as Administrator)
   mklink /D "%APPDATA%\Autodesk\Autodesk Fusion 360\API\Addins\FusionMCP" "C:\path\to\FusionMCP"

   # Mac/Linux
   ln -s /path/to/FusionMCP ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP
   ```

   **Option B - Copy Files**:
   Copy the entire FusionMCP project directory (including both `fusion360_addin` and `fusionmcp` folders) to the add-ins location.

3. **Configure Your AI Provider**:
   The add-in includes a `config.yaml` file in the `fusion360_addin` directory. Edit it to configure your preferred AI provider:

   **For Ollama (Local, Recommended)**:
   ```yaml
   ai_provider: "ollama"
   ollama_model: "llama3.1"
   ollama_url: "http://localhost:11434/api/generate"
   ```

   **For OpenAI**:
   ```yaml
   ai_provider: "openai"
   openai_api_key: "sk-your-api-key-here"
   openai_model: "gpt-3.5-turbo"
   ```

   **For Google Gemini**:
   ```yaml
   ai_provider: "gemini"
   gemini_api_key: "your-gemini-api-key-here"
   gemini_model: "gemini-pro"
   ```

4. **Install Python Dependencies**:
   Fusion 360 uses its own Python environment. Install dependencies system-wide:
   ```bash
   pip install -r requirements.txt
   ```

5. **Restart Fusion 360**:
   After installation, restart Fusion 360 to load the new add-in.

### Method 2: Standalone Add-in Installation (Production)

1. **Copy Add-in Files**:
   ```bash
   # Copy the entire fusion360_addin directory contents to Fusion 360 add-ins folder
   # The directory structure should be:
   # Addins/FusionMCP/
   #   ├── FusionMCP.py
   #   ├── config.yaml
   #   ├── manifest.json
   #   ├── resources/
   #   └── (copy fusionmcp package here)
   ```

2. **Ensure fusionmcp Package is Accessible**:
   Copy the `fusionmcp` directory to the same location as `FusionMCP.py` or ensure it's in Python's path.

## Using the Add-in

1. Once installed, you'll find the "FusionMCP" panel in the "MCP Tab" under the SolidModel workspace.

2. Click the "Start MCP" button to open the command dialog.

3. Enter your design request in the text box (e.g., "Create a cube with dimensions 10mm x 10mm x 10mm").

4. Choose whether to execute the generated script directly in Fusion 360.

## Configuration Options

The add-in supports all the same configuration options as the standalone version:

- OpenAI: Set `ai_provider: "openai"` with your API key
- Google Gemini: Set `ai_provider: "gemini"` with your API key
- Ollama: Set `ai_provider: "ollama"` with model and URL
- LM Studio: Set `ai_provider: "lm_studio"` with model and URL

## Troubleshooting

### Common Issues

1. **Add-in doesn't appear in Fusion 360**:
   - Verify the installation path is correct
   - Ensure the directory is named exactly "FusionMCP"
   - Restart Fusion 360
   - Check Scripts and Add-Ins panel for errors

2. **"Config file not found" error**:
   - Ensure `config.yaml` exists in the `fusion360_addin` directory
   - Check that the config file is valid YAML format
   - The add-in will search in these locations (in order):
     1. `fusion360_addin/config.yaml`
     2. `FusionMCP/config.yaml` (parent directory)
     3. `~/FusionMCP/config.yaml` (home directory)

3. **"Cannot connect to AI service" error**:
   - For Ollama: Ensure Ollama is running (`ollama serve`)
   - For LM Studio: Ensure LM Studio server is running and API is enabled
   - For OpenAI/Gemini: Check your API key is valid
   - Verify the URL in config.yaml is correct

4. **Import errors**:
   - Install required packages: `pip install -r requirements.txt`
   - Ensure Python version is 3.8 or higher
   - Check that `fusionmcp` package is accessible from the add-in

5. **Script execution fails**:
   - Check the Fusion 360 Text Commands window for detailed errors
   - Review the `execution_log.txt` file for debugging information
   - Ensure the generated script is valid Fusion 360 API code

### Debug Mode

To enable detailed logging:
1. Open Fusion 360's Text Commands window (View > Text Commands)
2. Look for FusionMCP log messages
3. Check `execution_log.txt` in the add-in directory

### Getting Help

- Check the main README.md for usage examples
- Review example scripts in the `examples` directory
- Report issues on the GitHub repository