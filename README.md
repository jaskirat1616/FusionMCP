# FusionMCP

FusionMCP (Multi-Modal Control Plane) is an intelligent interface that connects AI models to Autodesk Fusion 360, enabling automated CAD operations through natural language processing. The system allows users to describe design requirements in plain English, which are then converted into executable Fusion 360 Python scripts.

## Features

- **Natural Language Processing**: Convert plain English design requests into Fusion 360 commands
- **Multi-LLM Support**: Compatible with Gemini, Ollama, LM Studio, and OpenAI GPT models
- **Safe Script Execution**: Validates and executes generated scripts with safety checks
- **Context Management**: Maintains both short-term session context and long-term persistent memory
- **Plugin System**: Extensible architecture supporting external tools and APIs
- **Error Recovery**: Automatically attempts to fix script errors using AI
- **Fusion 360 Integration**: Designed as a Fusion 360 add-in for seamless workflow

## Installation

### Prerequisites

- Python 3.8 or higher
- Autodesk Fusion 360 (for add-in functionality)
- API keys for your chosen LLM provider (optional)

### Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd FusionMCP
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API keys (if using cloud-based LLMs):
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml to add your API keys
   ```

### For Fusion 360 Add-in

1. Install the add-in by copying the `fusion360_addin` directory to your Fusion 360 add-ins folder:
   - **Windows**: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Addins\FusionMCP`
   - **Mac**: `~/Library/Application Support/Autodesk/Autodesk Fusion 360\API/Addins/FusionMCP`
2. Restart Fusion 360
3. The add-in will appear in the MCP Tab under the SolidModel workspace

## Local LLM Setup (Ollama and LM Studio)

### Ollama Setup

1. Install Ollama from [https://ollama.com/](https://ollama.com/)
2. Start the Ollama service:
   ```bash
   ollama serve
   ```
3. Pull a model (e.g., Llama 3):
   ```bash
   ollama pull llama3
   ```
4. In your `config.yaml`, set:
   ```yaml
   ai_provider: "ollama"
   ollama_model: "llama3"
   ollama_url: "http://localhost:11434/api/generate"  # Default Ollama endpoint
   ```

### LM Studio Setup

1. Download and install LM Studio from [https://lmstudio.ai/](https://lmstudio.ai/)
2. Download a model (e.g., one of the Llama 3 models)
3. Start LM Studio and load your model
4. Click on the "Local Server (API)" button in the bottom left
5. In your `config.yaml`, set:
   ```yaml
   ai_provider: "lm_studio"
   lm_studio_model: "default"  # Keep as "default" for LM Studio
   lm_studio_url: "http://localhost:1234/v1/chat/completions"  # Default LM Studio API endpoint
   ```

## Configuration

The system can be configured via `config.yaml`:

```yaml
ai_provider: "openai"  # Can be "openai", "gemini", "ollama", or "lm_studio"
openai_api_key: "your-openai-api-key"
openai_model: "gpt-3.5-turbo"

gemini_api_key: "your-gemini-api-key"
gemini_model: "gemini-pro"

ollama_model: "llama3"
ollama_url: "http://localhost:11434/api/generate"

lm_studio_model: "default"
lm_studio_url: "http://localhost:1234/v1/chat/completions"

plugins:
  - name: "material_database"
    type: "internal"
    description: "Material properties database"
  
  - name: "file_converter"
    type: "external_app"
    command: "converter"
    args: ["-i", "{input_file}", "-o", "{output_file}", "-f", "{format}"]
```

## Usage

### Standalone Mode

Run the system in interactive mode:

```bash
python -m fusionmcp.fusion_mcp_main
```

Then enter your design requests:

```
FusionMCP> Create a cylinder with radius 5mm and height 10mm
```

### As a Fusion 360 Add-in (Real-time Integration)

The system now supports direct integration with Fusion 360 for real-time CAD operations:

1. **Install the Add-in**:
   - Locate your Fusion 360 add-ins directory:
     - **Windows**: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Addins`
     - **Mac**: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Addins`
   - Create a new folder named `FusionMCP`
   - Copy all files from the `fusion360_addin/` directory to this folder
   - Restart Fusion 360

2. **Access the Interface**:
   - Open Fusion 360
   - Navigate to the "MCP Tab" in the SolidModel workspace
   - Click the "Start MCP" button to open the command dialog

3. **Use Natural Language**:
   - Enter your design requests in the text box (e.g., "Create a cube with dimensions 10mm x 10mm x 10mm")
   - Choose whether to execute directly in Fusion 360
   - The AI will generate and execute Fusion 360 scripts in real-time

### Example Requests

- "Create a cube with dimensions 10mm x 10mm x 10mm"
- "Draw a circle with radius 20mm at coordinates (5, 5)"
- "Extrude the sketch by 15mm"
- "Create a revolved feature from the selected profile"
- "Create a cylinder with radius 3mm and height 15mm at the origin"

## Architecture

The system consists of several key components:

### Context Manager
- Manages both session and persistent context
- Implements context summarization to save tokens
- Stores interaction history and state

### AI Interface
- Abstracts access to multiple LLM providers
- Handles API calls, errors, and authentication
- Generates Fusion 360 Python scripts from natural language

### Command Executor
- Validates scripts to prevent destructive operations
- Safely executes Fusion 360 commands
- Logs execution results and errors

### Plugin Manager
- Extensible system for external tool integration
- Allows AI to call external applications or APIs
- Includes example plugins for material database and file conversion

### Main Orchestrator
- Coordinates all components
- Manages user interaction flow
- Provides both console and dialog interfaces

## Example Workflow

The example workflow demonstrates the complete pipeline:

```python
from fusionmcp.fusion_mcp_main import FusionMCP

# Initialize the system
mcp = FusionMCP()

# Process a user request
result = mcp.process_request("Create a cube with dimensions 10mm x 10mm x 10mm")

# The system will:
# 1. Generate a Fusion 360 script from the request
# 2. Validate the script for safety
# 3. Execute the script in Fusion 360
# 4. Return the result to the user
```

Run the example with:

```bash
python examples/example_workflow.py
```

## Dependencies

See `requirements.txt` for a complete list of dependencies. Key dependencies include:

- `requests` - for API calls
- `pyyaml` - for configuration
- `google-generativeai` - for Gemini API
- `adsk` - Fusion 360 Python API (available in Fusion 360 environment)

## Development

To run tests and examples:

```bash
# Run the example workflow
python examples/example_workflow.py

# Run in interactive mode
python -m fusionmcp.fusion_mcp_main
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Specify your license here]

## Support

For support, please open an issue in the GitHub repository or contact [your contact information].