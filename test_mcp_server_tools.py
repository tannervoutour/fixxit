#!/usr/bin/env python3
"""Test MCP server tools by calling them directly through the server."""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-sdk'))

async def test_mcp_server():
    """Test the MCP server tools after our fixes."""
    
    print("🧪 Testing MCP Server with Fixed Tools...")
    print("=" * 60)
    
    try:
        # We'll simulate what the MCP client does
        from openai_mcp_client.mcp_bridge import MCPBridge
        
        # Create MCP bridge
        mcp_bridge = MCPBridge()
        
        # Connect to the server
        print("🔗 Connecting to MCP server...")
        success = await mcp_bridge.connect()
        
        if not success:
            print("❌ Failed to connect to MCP server")
            return False
            
        print("✅ Connected to MCP server")
        
        # Test the search_machine_docs tool (this maps to our fixed function)
        print("\n📝 Testing search_machine_docs with 'Tunnels'...")
        
        result = await mcp_bridge.call_tool(
            "search_machine_docs",
            {"machine_name": "Tunnels"}
        )
        
        print("🎯 Result:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success', False):
            print("✅ Tool call succeeded!")
            
            # Parse the JSON result
            import json
            if 'result' in result:
                tool_result = json.loads(result['result']) if isinstance(result['result'], str) else result['result']
                
                if tool_result.get('success', False):
                    print(f"   Machines found: {tool_result.get('machines_found', 0)}")
                    
                    for machine in tool_result.get('machines', []):
                        print(f"   📋 {machine['machine_name']} ({machine['machine_type']})")
                        print(f"      Documents: {machine['document_count']}, Sections: {machine['section_count']}")
                else:
                    print(f"   ❌ Tool returned error: {tool_result.get('error', 'Unknown')}")
            
        else:
            print(f"❌ Tool call failed: {result}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    if success:
        print(f"\n🎉 SUCCESS: MCP tools are working after the fix!")
    else:
        print(f"\n❌ FAILURE: MCP tools still not working")