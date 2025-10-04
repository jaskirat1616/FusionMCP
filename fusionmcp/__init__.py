"""
FusionMCP - Multi-Modal Control Plane for Fusion 360

This package provides an intelligent interface between AI models and Fusion 360,
enabling automated CAD operations through natural language processing.
"""

__version__ = "1.0.0"
__author__ = "FusionMCP Development Team"

# Import key modules for easy access
from .context_manager import ContextManager
from .ai_interface import AIInterface
from .command_executor import CommandExecutor
from .fusion_command_executor import FusionCommandExecutor
from .plugin_manager import PluginManager
from .fusion_mcp_main import FusionMCP