# Installation Guide for FusionMCP Add-in

## Prerequisites
- Autodesk Fusion 360
- Ollama running with a compatible model (e.g., llama3.1)

## Installation Steps

1. **Prepare the Add-in Directory**:
   Fusion 360 add-ins are typically stored in one of these locations:
   
   **Windows**:
   ```
   %APPDATA%\Autodesk\Autodesk Fusion 360\API\Addins\FusionMCP
   ```
   
   **Mac**:
   ```
   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Addins/FusionMCP
   ```

2. **Copy the Add-in Files**:
   Copy the entire `fusion360_addin` directory to the appropriate location mentioned above.

3. **Install Dependencies**:
   Fusion 360 runs its own Python interpreter, so dependencies must be accessible within Fusion 360's environment. The core FusionMCP modules (in the `fusionmcp` directory) need to be accessible to the add-in.

4. **Configure FusionMCP**:
   You'll need a `config.yaml` file in the Fusion 360 documents directory or in the add-in folder with your preferred AI provider configuration:
   ```yaml
   ai_provider: "ollama"
   ollama_model: "llama3.1"
   ollama_url: "http://localhost:11434/api/generate"
   ```

5. **Restart Fusion 360**:
   After installation, restart Fusion 360 to load the new add-in.

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

- Ensure Ollama (or your chosen LLM service) is running before using the add-in
- Check that all required Python files are accessible to Fusion 360
- If the add-in doesn't appear, verify the installation path and restart Fusion 360
- Check the Fusion 360 script output window for any error messages