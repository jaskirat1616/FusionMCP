#!/bin/bash
# FusionMCP Add-in Installation Script for macOS

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           FusionMCP Add-in Installer for macOS                    ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Define paths
ADDIN_DIR=~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Addins
PROJECT_DIR="/Users/jaskiratsingh/Desktop/FusionMCP"

# Create addins directory if it doesn't exist
if [ ! -d "$ADDIN_DIR" ]; then
    echo "📁 Creating Fusion 360 add-ins directory..."
    mkdir -p "$ADDIN_DIR"
fi

# Remove existing symlink/folder if exists
if [ -e "$ADDIN_DIR/FusionMCP" ]; then
    echo "🗑️  Removing existing FusionMCP installation..."
    rm -rf "$ADDIN_DIR/FusionMCP"
fi

# Create symbolic link
echo "🔗 Creating symbolic link..."
ln -s "$PROJECT_DIR" "$ADDIN_DIR/FusionMCP"

# Verify installation
if [ -L "$ADDIN_DIR/FusionMCP" ]; then
    echo ""
    echo "✅ SUCCESS! FusionMCP add-in installed!"
    echo ""
    echo "📋 Installation Details:"
    echo "   Source: $PROJECT_DIR"
    echo "   Link:   $ADDIN_DIR/FusionMCP"
    echo ""
    echo "🚀 Next Steps:"
    echo "   1. Start Ollama: ollama serve"
    echo "   2. Open Fusion 360"
    echo "   3. Press Shift+S to open Scripts and Add-Ins"
    echo "   4. Select 'FusionMCP' and click 'Run'"
    echo "   5. Look for 'MCP Tab' in the toolbar"
    echo ""
else
    echo "❌ Installation failed. Please check permissions."
    exit 1
fi
