"""Configuration settings for the OpenAI MCP client."""

import os
from pathlib import Path
from typing import Optional


class ClientConfig:
    """Configuration class for the OpenAI MCP maintenance client."""
    
    # Client identification
    CLIENT_NAME = "OpenAI MCP Maintenance Assistant"
    CLIENT_VERSION = "1.0.0"
    CLIENT_DESCRIPTION = "AI assistant for machine maintenance using OpenAI GPT-4o and MCP"
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o"
    MAX_TOKENS = 4000
    TEMPERATURE = 0.1  # Low temperature for consistent, factual responses
    
    # MCP server configuration
    MCP_SERVER_PATH = Path(__file__).parent.parent / "mcp-sqlite-server" / "server.py"
    MCP_CONNECTION_TIMEOUT = 30  # seconds
    MCP_COMMAND_TIMEOUT = 60  # seconds
    
    # Conversation settings
    MAX_CONVERSATION_HISTORY = 20  # messages to keep in memory
    CONTEXT_RETENTION_TURNS = 5  # how many turns to remember entities
    MAX_TOOL_ITERATIONS = 20  # maximum tool calls per query (increased for complex documentation queries)
    
    # Response formatting
    ENABLE_RICH_FORMATTING = True
    MAX_TABLE_ROWS = 20  # limit displayed rows in tables
    TRUNCATE_LONG_RESPONSES = True
    
    # System prompts
    SYSTEM_PROMPT = """You are a helpful AI assistant specializing in machine maintenance and troubleshooting. 

You have access to a comprehensive maintenance database through specialized tools. Use these tools to:
- Find machines by location, status, model, or manufacturer
- Look up trouble tickets and their current status
- Check maintenance history and service records  
- Search parts inventory and stock levels
- Get troubleshooting steps for fault codes
- Find technician expertise and availability

Key guidelines:
1. Always use the appropriate tool when users ask about specific data
2. Be proactive in suggesting related information that might be helpful
3. Format responses clearly with relevant details highlighted
4. Remember context from previous queries to handle follow-up questions
5. Prioritize urgent issues and safety concerns
6. Provide actionable next steps when possible

When a user asks about maintenance issues, think about what information they might need and gather it proactively."""

    @classmethod
    def get_openai_api_key(cls) -> str:
        """Get OpenAI API key from environment or config."""
        return os.getenv("OPENAI_API_KEY") or cls.OPENAI_API_KEY
    
    @classmethod
    def get_mcp_server_path(cls) -> str:
        """Get MCP server path."""
        env_path = os.getenv("MCP_SERVER_PATH")
        if env_path:
            return env_path
        return str(cls.MCP_SERVER_PATH)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        api_key = cls.get_openai_api_key()
        if not api_key or api_key.startswith("your-"):
            print("❌ Error: OpenAI API key not configured")
            return False
        
        server_path = Path(cls.get_mcp_server_path())
        if not server_path.exists():
            print(f"❌ Error: MCP server not found at {server_path}")
            return False
        
        return True
    
    @classmethod
    def get_client_info(cls) -> dict:
        """Get client information dictionary."""
        return {
            "name": cls.CLIENT_NAME,
            "version": cls.CLIENT_VERSION,
            "description": cls.CLIENT_DESCRIPTION,
            "model": cls.OPENAI_MODEL,
            "mcp_server": cls.get_mcp_server_path()
        }


# Global configuration instance
config = ClientConfig()