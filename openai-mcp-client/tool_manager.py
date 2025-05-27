"""Dynamic tool management system for loading and filtering AI tools."""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dotenv import load_dotenv


class ToolManager:
    """Manages dynamic loading and filtering of AI tools based on configuration."""
    
    def __init__(self, 
                 registry_path: str = "/root/fixxitV2/tool_registry.yaml",
                 config_path: str = "/root/fixxitV2/tool_config.env"):
        """
        Initialize the tool manager.
        
        Args:
            registry_path: Path to the tool registry YAML file
            config_path: Path to the tool configuration .env file
        """
        self.registry_path = Path(registry_path)
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Tool data storage
        self.tool_registry: Dict[str, Any] = {}
        self.tool_config: Dict[str, bool] = {}
        self.enabled_tools: Set[str] = set()
        self.always_available: Set[str] = set()
        
        # Load initial configuration
        self.load_registry()
        self.load_config()
        self.update_enabled_tools()
    
    def load_registry(self) -> bool:
        """Load the tool registry from YAML file."""
        try:
            if not self.registry_path.exists():
                self.logger.error(f"Tool registry not found: {self.registry_path}")
                return False
            
            with open(self.registry_path, 'r') as f:
                data = yaml.safe_load(f)
            
            self.tool_registry = data.get('tools', {})
            self.always_available = set(data.get('always_available', []))
            
            self.logger.info(f"✅ Loaded {len(self.tool_registry)} tools from registry")
            self.logger.info(f"📌 Always available tools: {list(self.always_available)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load tool registry: {e}")
            return False
    
    def load_config(self) -> bool:
        """Load the tool configuration from .env file."""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Tool config not found: {self.config_path} - using defaults")
                return False
            
            # Parse configuration file directly (not using environment variables)
            self.tool_config = {}
            
            with open(self.config_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        try:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().lower()
                            
                            # Find which tool this config controls
                            for tool_name, tool_def in self.tool_registry.items():
                                if tool_def.get('enabled_by') == key:
                                    self.tool_config[tool_name] = value in ('true', '1', 'yes', 'on')
                                    break
                        except ValueError:
                            self.logger.warning(f"Invalid config line {line_num}: {line}")
            
            enabled_count = sum(1 for enabled in self.tool_config.values() if enabled)
            self.logger.info(f"⚙️ Loaded config - {enabled_count}/{len(self.tool_config)} tools enabled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load tool config: {e}")
            return False
    
    def update_enabled_tools(self):
        """Update the set of enabled tools based on current configuration."""
        self.enabled_tools = set()
        
        # Add always available tools
        self.enabled_tools.update(self.always_available)
        
        # Add configured tools that are enabled
        for tool_name, is_enabled in self.tool_config.items():
            if is_enabled:
                self.enabled_tools.add(tool_name)
        
        self.logger.info(f"🔧 Active tools: {sorted(list(self.enabled_tools))}")
    
    def get_enabled_functions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI function definitions for all enabled tools.
        
        Returns:
            List of function definitions ready for OpenAI API
        """
        functions = []
        
        # Always add the answer function
        functions.append(self._create_answer_function())
        
        # Add enabled tools
        for tool_name in self.enabled_tools:
            if tool_name in self.tool_registry and tool_name != "answer_user_query":
                function_def = self._create_function_definition(tool_name)
                if function_def:
                    functions.append(function_def)
        
        self.logger.info(f"📋 Generated {len(functions)} function definitions")
        return functions
    
    def _create_answer_function(self) -> Dict[str, Any]:
        """Create the answer_user_query function definition."""
        return {
            "type": "function",
            "function": {
                "name": "answer_user_query",
                "description": "Provides the final answer to the user's question based on information gathered from previous tool calls.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "The concise answer to the user's original question based on all gathered information."
                        }
                    },
                    "required": ["answer"],
                    "additionalProperties": False
                }
            }
        }
    
    def _create_function_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Create an OpenAI function definition from a tool registry entry.
        
        Args:
            tool_name: Name of the tool in the registry
            
        Returns:
            OpenAI function definition or None if invalid
        """
        try:
            tool_def = self.tool_registry[tool_name]
            
            # Build parameters object
            properties = {}
            required = []
            
            for param_name, param_def in tool_def.get('parameters', {}).items():
                properties[param_name] = {
                    "type": param_def["type"],
                    "description": param_def["description"]
                }
                
                # Add enum if specified
                if "enum" in param_def:
                    properties[param_name]["enum"] = param_def["enum"]
                
                # Add default if specified
                if "default" in param_def:
                    properties[param_name]["default"] = param_def["default"]
                
                # Check if required
                if param_def.get("required", False):
                    required.append(param_name)
            
            # Build the complete function definition
            function_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_def["description"],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "additionalProperties": False
                    }
                }
            }
            
            # Add required fields if any
            if required:
                function_def["function"]["parameters"]["required"] = required
            
            return function_def
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create function definition for {tool_name}: {e}")
            return None
    
    def get_mcp_mapping(self) -> Dict[str, str]:
        """
        Get the mapping from OpenAI function names to MCP tool names.
        
        Returns:
            Dictionary mapping function names to MCP tool names
        """
        mapping = {}
        
        # Add special answer function
        mapping["answer_user_query"] = None
        
        # Add enabled tools
        for tool_name in self.enabled_tools:
            if tool_name in self.tool_registry and tool_name != "answer_user_query":
                mcp_function = self.tool_registry[tool_name].get('mcp_function')
                if mcp_function:
                    mapping[tool_name] = mcp_function
        
        return mapping
    
    def get_parameter_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Get parameter mapping for function calls.
        
        Returns:
            Dictionary mapping function names to their parameter mappings
        """
        param_mapping = {}
        
        # Add special answer function
        param_mapping["answer_user_query"] = {"answer": "answer"}
        
        # Add enabled tools
        for tool_name in self.enabled_tools:
            if tool_name in self.tool_registry and tool_name != "answer_user_query":
                # Create 1:1 parameter mapping (param_name -> param_name)
                tool_params = self.tool_registry[tool_name].get('parameters', {})
                param_mapping[tool_name] = {name: name for name in tool_params.keys()}
        
        return param_mapping
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a specific tool is enabled.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool is enabled, False otherwise
        """
        return tool_name in self.enabled_tools
    
    def get_enabled_tools_by_category(self, category: str) -> List[str]:
        """
        Get all enabled tools in a specific category.
        
        Args:
            category: Category name to filter by
            
        Returns:
            List of enabled tool names in the category
        """
        enabled_in_category = []
        
        for tool_name in self.enabled_tools:
            if tool_name in self.tool_registry:
                tool_category = self.tool_registry[tool_name].get('category')
                if tool_category == category:
                    enabled_in_category.append(tool_name)
        
        return enabled_in_category
    
    def reload_config(self) -> bool:
        """
        Reload the configuration file and update enabled tools.
        
        Returns:
            True if reload was successful, False otherwise
        """
        self.logger.info("🔄 Reloading tool configuration...")
        
        if self.load_config():
            self.update_enabled_tools()
            self.logger.info("✅ Tool configuration reloaded successfully")
            return True
        else:
            self.logger.error("❌ Failed to reload tool configuration")
            return False
    
    def get_tool_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all tools.
        
        Returns:
            Dictionary with tool status information
        """
        return {
            "total_tools": len(self.tool_registry),
            "enabled_tools": len(self.enabled_tools),
            "always_available": list(self.always_available),
            "enabled_list": sorted(list(self.enabled_tools)),
            "disabled_list": sorted([name for name in self.tool_registry.keys() 
                                   if name not in self.enabled_tools]),
            "categories": {
                cat: self.get_enabled_tools_by_category(cat) 
                for cat in set(tool.get('category') for tool in self.tool_registry.values() if tool.get('category'))
            }
        }


# Global tool manager instance
tool_manager = ToolManager()