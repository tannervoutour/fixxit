"""MCP bridge for connecting to the SQLite maintenance server."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import config
from function_definitions import get_function_to_mcp_mapping, get_parameter_mapping


class MCPBridge:
    """Bridge to connect OpenAI client to MCP SQLite server."""
    
    def __init__(self):
        """Initialize the MCP bridge."""
        self.session: Optional[ClientSession] = None
        self.stdio_context = None
        self.server_process: Optional[subprocess.Popen] = None
        self.is_connected = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    async def connect(self) -> bool:
        """Connect to the MCP SQLite server."""
        try:
            # Get server path
            server_path = config.get_mcp_server_path()
            if not Path(server_path).exists():
                self.logger.error(f"MCP server not found at: {server_path}")
                return False
            
            # Create server parameters for stdio connection
            # We need to run the server using the UV environment from main project directory
            project_root = Path(server_path).parent.parent
            
            server_params = StdioServerParameters(
                command="python",
                args=[server_path],
                env=None,
                cwd=str(project_root)
            )
            
            # Connect to the server
            self.logger.info(f"Connecting to MCP server: {server_path}")
            
            # Start the stdio client and store the context manager
            self.stdio_context = stdio_client(server_params)
            read_stream, write_stream = await self.stdio_context.__aenter__()
            
            # Create client session
            self.session = ClientSession(read_stream, write_stream)
            await self.session.__aenter__()
            
            # Initialize the connection
            await self.session.initialize()
            
            self.is_connected = True
            self.logger.info("✅ Successfully connected to MCP server")
            
            # Test the connection by listing available tools
            tools = await self.session.list_tools()
            tool_names = []
            for tool in tools:
                if hasattr(tool, 'name'):
                    tool_names.append(tool.name)
                else:
                    tool_names.append(str(tool))
            self.logger.info(f"📋 Available tools: {tool_names}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
                self.session = None
            
            if self.stdio_context:
                await self.stdio_context.__aexit__(None, None, None)
                self.stdio_context = None
            
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
            
            self.is_connected = False
            self.logger.info("🔌 Disconnected from MCP server")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
    
    async def call_function(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an OpenAI function by translating it to the appropriate MCP tool.
        
        Args:
            function_name: OpenAI function name
            parameters: Function parameters
            
        Returns:
            Dict with function result or error
        """
        # Handle special answer function
        if function_name == "answer_user_query":
            return {
                "success": True,
                "data": parameters.get("answer", "No answer provided"),
                "function": function_name
            }
        
        if not self.is_connected or not self.session:
            return {
                "error": "Not connected to MCP server",
                "function": function_name
            }
        
        try:
            # Map OpenAI function to MCP tool using dynamic mapping
            function_mapping = get_function_to_mcp_mapping()
            mcp_tool_name = function_mapping.get(function_name)
            if not mcp_tool_name:
                return {
                    "error": f"Unknown function: {function_name}",
                    "function": function_name
                }
            
            # Map parameters
            mcp_parameters = self._map_parameters(function_name, parameters)
            
            self.logger.info(f"🔧 Calling MCP tool: {mcp_tool_name} with params: {mcp_parameters}")
            
            # Call the MCP tool
            result = await self.session.call_tool(mcp_tool_name, mcp_parameters)
            
            # Parse the JSON response from MCP tool
            if hasattr(result, 'content') and result.content:
                # Handle list of content items
                if isinstance(result.content, list) and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        response_text = content.text
                    else:
                        response_text = str(content)
                else:
                    response_text = str(result.content)
                
                try:
                    # Try to parse as JSON
                    parsed_result = json.loads(response_text)
                    return {
                        "success": True,
                        "function": function_name,
                        "mcp_tool": mcp_tool_name,
                        "result": parsed_result
                    }
                except json.JSONDecodeError:
                    # Return as text if not JSON
                    return {
                        "success": True,
                        "function": function_name,
                        "mcp_tool": mcp_tool_name,
                        "result": {"text": response_text}
                    }
            else:
                return {
                    "error": "Empty response from MCP server",
                    "function": function_name,
                    "mcp_tool": mcp_tool_name
                }
                
        except Exception as e:
            self.logger.error(f"Error calling MCP tool {mcp_tool_name}: {e}")
            return {
                "error": f"MCP tool call failed: {str(e)}",
                "function": function_name,
                "mcp_tool": mcp_tool_name if mcp_tool_name else "unknown"
            }
    
    def _map_parameters(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Map OpenAI function parameters to MCP tool parameters."""
        parameter_mapping = get_parameter_mapping()
        mapping = parameter_mapping.get(function_name, {})
        
        mapped_params = {}
        for openai_param, value in parameters.items():
            # Get the MCP parameter name (or use the same name if no mapping)
            mcp_param = mapping.get(openai_param, openai_param)
            mapped_params[mcp_param] = value
        
        return mapped_params
    
    async def get_available_tools(self) -> Optional[list]:
        """Get list of available tools from the MCP server."""
        if not self.is_connected or not self.session:
            return None
        
        try:
            tools = await self.session.list_tools()
            tool_list = []
            for tool in tools:
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    tool_list.append({"name": tool.name, "description": tool.description})
                else:
                    tool_list.append({"name": str(tool), "description": "Unknown"})
            return tool_list
        except Exception as e:
            self.logger.error(f"Error getting tools: {e}")
            return None
    
    async def get_available_resources(self) -> Optional[list]:
        """Get list of available resources from the MCP server."""
        if not self.is_connected or not self.session:
            return None
        
        try:
            resources = await self.session.list_resources()
            return [{"uri": resource.uri, "name": resource.name, "description": resource.description} 
                   for resource in resources]
        except Exception as e:
            self.logger.error(f"Error getting resources: {e}")
            return None
    
    async def read_resource(self, resource_uri: str) -> Optional[Dict[str, Any]]:
        """Read a specific resource from the MCP server."""
        if not self.is_connected or not self.session:
            return None
        
        try:
            content, mime_type = await self.session.read_resource(resource_uri)
            return {
                "content": content,
                "mime_type": mime_type,
                "uri": resource_uri
            }
        except Exception as e:
            self.logger.error(f"Error reading resource {resource_uri}: {e}")
            return None


# Global MCP bridge instance
mcp_bridge = MCPBridge()