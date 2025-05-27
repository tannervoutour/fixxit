"""Dynamic function definitions using the tool management system."""

from typing import Dict, List, Any
from tool_manager import tool_manager


class FunctionDefinitions:
    """Dynamic function definitions loaded from tool registry."""
    
    @staticmethod
    def get_all_functions() -> List[Dict[str, Any]]:
        """Get all enabled function definitions for OpenAI."""
        return tool_manager.get_enabled_functions()
    
    @staticmethod
    def get_function_to_mcp_mapping() -> Dict[str, str]:
        """Get mapping from OpenAI function names to MCP tool names."""
        return tool_manager.get_mcp_mapping()
    
    @staticmethod
    def get_parameter_mapping() -> Dict[str, Dict[str, str]]:
        """Get parameter mapping for function calls."""
        return tool_manager.get_parameter_mapping()
    
    @staticmethod
    def is_tool_enabled(tool_name: str) -> bool:
        """Check if a specific tool is enabled."""
        return tool_manager.is_tool_enabled(tool_name)
    
    @staticmethod
    def reload_tools() -> bool:
        """Reload tool configuration from files."""
        return tool_manager.reload_config()


# Legacy mappings for backward compatibility
# These are now dynamically generated from tool_manager
FUNCTION_TO_MCP_MAPPING = None  # Will be set by dynamic loading
PARAMETER_MAPPING = None  # Will be set by dynamic loading

def get_function_to_mcp_mapping() -> Dict[str, str]:
    """Get current function to MCP mapping."""
    return FunctionDefinitions.get_function_to_mcp_mapping()

def get_parameter_mapping() -> Dict[str, Dict[str, str]]:
    """Get current parameter mapping."""
    return FunctionDefinitions.get_parameter_mapping()