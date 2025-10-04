# FusionMCP Fusion 360 Add-in

This add-in integrates the FusionMCP Multi-Modal Control Plane directly into Autodesk Fusion 360, allowing you to interact with AI models to create and modify CAD models in real-time.

## Features

- Natural language to CAD conversion directly within Fusion 360
- Support for multiple AI backends (Ollama, LM Studio, OpenAI, Gemini)
- Real-time script generation and execution
- Context-aware design assistant
- Plugin system for extended functionality

## Usage

1. Install the add-in following the instructions in INSTALL.md
2. Start Ollama (or your preferred AI service) with the model of your choice
3. Open Fusion 360 and navigate to the MCP Tab
4. Click "Start MCP" and enter your design request
5. The AI will generate a Fusion 360 script and execute it in real-time

## Supported Commands

The AI system understands a wide variety of CAD commands including:

- Basic shapes: cubes, cylinders, spheres, cones
- Sketch operations: lines, circles, rectangles, polygons
- Feature operations: extrude, revolve, sweep, loft
- Modification: fillet, chamfer, shell, pattern
- Assembly operations: constraints, joints

Example requests:
- "Create a cube with dimensions 10mm x 10mm x 10mm"
- "Draw a circle with radius 5mm centered at origin"
- "Extrude the sketch by 15mm"
- "Create a cylinder with radius 3mm and height 20mm"

## Configuration

The add-in reads configuration from a config.yaml file, which determines which AI provider to use and related settings.

## Safety

The system includes multiple safety checks to prevent destructive operations and validate all generated scripts before execution.