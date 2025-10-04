# FusionMCP Quick Start Guide

## Installation & Testing Guide

### Step 1: Install the Fusion 360 Add-in

#### On macOS:

1. **Locate the Fusion 360 Add-ins Directory**:
   ```bash
   cd ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins
   ```
   
   If the directory doesn't exist, create it:
   ```bash
   mkdir -p ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins
   ```

2. **Create a Symbolic Link** (Recommended for development):
   ```bash
   # Navigate to the Addins folder
   cd ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins
   
   # Create symbolic link to your FusionMCP project
   ln -s /Users/jaskiratsingh/Desktop/FusionMCP FusionMCP
   ```
   
   OR **Copy the Files** (Alternative method):
   ```bash
   # Copy the entire FusionMCP directory
   cp -r /Users/jaskiratsingh/Desktop/FusionMCP ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP
   ```

3. **Verify the Structure**:
   ```bash
   ls -la ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP
   ```
   
   You should see:
   - `fusion360_addin/` folder
   - `fusionmcp/` folder
   - `config.yaml`
   - `README.md`
   - etc.

#### On Windows:

1. **Locate the Add-ins Directory**:
   ```
   %APPDATA%\Autodesk\Autodesk Fusion 360\API\Addins
   ```
   
2. **Create a Symbolic Link** (Run as Administrator):
   ```cmd
   cd %APPDATA%\Autodesk\Autodesk Fusion 360\API\Addins
   mklink /D FusionMCP "C:\path\to\your\FusionMCP"
   ```
   
   OR **Copy the Folder**:
   - Copy the entire FusionMCP folder to the Addins directory

---

### Step 2: Configure AI Provider

**Before starting Fusion 360**, configure your AI provider:

#### Option A: Use Ollama (Recommended - Free & Local)

1. **Install Ollama**:
   ```bash
   # Download from https://ollama.com/
   # Or on macOS:
   brew install ollama
   ```

2. **Start Ollama**:
   ```bash
   ollama serve
   ```
   
   (Keep this terminal open)

3. **Pull a Model** (in a new terminal):
   ```bash
   ollama pull llama3.1
   ```

4. **Config is Already Set**:
   The `fusion360_addin/config.yaml` is already configured for Ollama!

#### Option B: Use OpenAI

1. **Edit config**:
   ```bash
   nano ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP/fusion360_addin/config.yaml
   ```

2. **Change these lines**:
   ```yaml
   ai_provider: "openai"
   openai_api_key: "sk-your-actual-api-key-here"
   openai_model: "gpt-3.5-turbo"
   ```

---

### Step 3: Start Fusion 360

1. **Open Fusion 360**

2. **Check Scripts and Add-Ins Panel**:
   - Go to: **Utilities** > **ADD-INS** > **Scripts and Add-Ins** (or press `Shift + S`)

3. **Look for FusionMCP**:
   - Under "Add-Ins" tab
   - You should see "FusionMCP" in the list
   - If you see an error, check the error message

4. **Run the Add-in**:
   - Select "FusionMCP"
   - Click "Run"
   - (Optionally check "Run on Startup" for automatic loading)

5. **Find the MCP Tab**:
   - After running, look for a new tab called "MCP Tab" in the toolbar
   - Click on it
   - You should see a "Start MCP" button

---

### Step 4: Test the Add-in

#### Test 1: Open the Interface

1. Click **"Start MCP"** button
2. A dialog should appear with:
   - Text box for entering requests
   - "Execute" checkbox
   - OK/Cancel buttons

#### Test 2: Simple Cube Test

1. In the dialog, enter:
   ```
   Create a cube with dimensions 10mm x 10mm x 10mm
   ```

2. Check the "Execute" checkbox

3. Click "OK"

4. **Expected Result**:
   - The AI generates a Fusion 360 script
   - The script executes
   - A 10mm cube appears in your design!

#### Test 3: Simple Cylinder Test

1. Click "Start MCP" again
2. Enter:
   ```
   Create a cylinder with radius 5mm and height 20mm
   ```
3. Click OK

4. **Expected Result**:
   - A cylinder appears in your design

#### Test 4: Plugin Test

1. Click "Start MCP"
2. Enter:
   ```
   What is the density of aluminum?
   ```
3. **Expected Result**:
   - Material database plugin executes
   - Returns: "Density: 2.7 g/cm³"

---

### Troubleshooting

#### Issue: Add-in doesn't appear

**Solution 1**: Check the path
```bash
ls -la ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP
```

**Solution 2**: Check for errors
- Open Scripts and Add-Ins (Shift + S)
- Look for error messages next to FusionMCP
- Check the Text Commands window (View > Text Commands)

#### Issue: "Config file not found"

**Solution**: Copy config to add-in directory
```bash
cp /Users/jaskiratsingh/Desktop/FusionMCP/config.yaml \
   ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP/fusion360_addin/
```

#### Issue: "Cannot connect to AI service"

**For Ollama**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/generate

# If not running:
ollama serve
```

**For OpenAI**:
- Verify your API key is correct in `config.yaml`
- Check you have API credits

#### Issue: Script execution fails

**Check Text Commands window**:
- View > Text Commands
- Look for detailed error messages
- Check `execution_log.txt` in the add-in directory

#### Issue: Python import errors

**Install dependencies**:
```bash
# Fusion 360 uses system Python, install globally:
pip3 install -r /Users/jaskiratsingh/Desktop/FusionMCP/requirements.txt

# Or:
pip3 install requests pyyaml google-generativeai openai
```

---

### Alternative: Test Without Fusion 360 First

Before installing in Fusion 360, test standalone mode:

```bash
cd /Users/jaskiratsingh/Desktop/FusionMCP

# Make sure Ollama is running (if using Ollama)
ollama serve  # in another terminal

# Test standalone
python3 -m fusionmcp.fusion_mcp_main
```

Commands to try:
- `plugins`
- `material steel`
- `material aluminum`

This verifies everything works before Fusion 360 integration.

---

### Quick Command Reference

```bash
# Create symbolic link (recommended)
ln -s /Users/jaskiratsingh/Desktop/FusionMCP \
      ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP

# Start Ollama
ollama serve

# Pull model (first time only)
ollama pull llama3.1

# Test standalone
python3 -m fusionmcp.fusion_mcp_main

# Check add-in is installed
ls -la ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins/FusionMCP
```

---

### Success Indicators

✅ Add-in appears in Scripts and Add-Ins panel
✅ "MCP Tab" appears in toolbar after running add-in
✅ "Start MCP" button is visible
✅ Dialog opens when clicking "Start MCP"
✅ AI generates scripts from natural language
✅ Scripts execute and create geometry

---

### Example Prompts to Try

Once working, try these:

1. **Basic Shapes**:
   - "Create a sphere with radius 15mm"
   - "Make a box 20x30x10mm"
   
2. **Sketches**:
   - "Draw a circle with radius 10mm at the origin"
   - "Create a rectangle 50mm by 30mm"
   
3. **Features**:
   - "Extrude the last sketch by 25mm"
   - "Create a fillet with radius 2mm on all edges"

4. **Plugins**:
   - "What are the properties of steel?"
   - "Get density of plastic"

---

### Getting Help

- Check `fusion360_addin/INSTALL.md` for detailed installation
- Check `FIXES_APPLIED.md` for what was fixed
- Check `execution_log.txt` for detailed errors
- Open issue on GitHub: https://github.com/jaskirat1616/FusionMCP/issues

---

## Next Steps

1. ✅ Install add-in (symbolic link)
2. ✅ Start Ollama (if using Ollama)
3. ✅ Open Fusion 360
4. ✅ Run add-in from Scripts and Add-Ins
5. ✅ Click "Start MCP"
6. ✅ Test with simple commands
7. 🎉 Start creating with natural language!

---

**You're ready to go! Good luck with your AI-powered CAD design!** 🚀
