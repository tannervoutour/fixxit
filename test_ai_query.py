#!/usr/bin/env python3
"""
Test the AI system with a specific documentation query.
"""

import os
import sys
import asyncio
from pathlib import Path

# Set the OpenAI API key
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

# Add the openai-mcp-client directory to the path
sys.path.insert(0, str(Path(__file__).parent / "openai-mcp-client"))

async def test_ai_query():
    """Test a specific AI query about machine documentation."""
    
    try:
        from openai_manager import OpenAIManager
        from mcp_bridge import MCPBridge
        from tool_manager import ToolManager
        
        print("🤖 Testing AI Documentation Query")
        print("=" * 50)
        
        # Initialize tool manager
        tool_manager = ToolManager()
        
        # Initialize MCP bridge
        mcp_bridge = MCPBridge(server_path="/root/fixxitV2/mcp-sqlite-server/server.py")
        await mcp_bridge.connect()
        
        # Initialize OpenAI manager
        openai_manager = OpenAIManager(tool_manager, mcp_bridge)
        
        # Test query about PowerPress safety
        query = "What safety procedures are documented for the PowerPress machine?"
        
        print(f"🔍 Query: {query}")
        print("\n🤖 AI Response:")
        print("-" * 50)
        
        response = await openai_manager.process_message(query)
        print(response)
        
        print("\n✅ AI query completed successfully!")
        
        # Cleanup
        await mcp_bridge.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_query())