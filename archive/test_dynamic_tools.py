#!/usr/bin/env python3
"""Test script for dynamic tool management system."""

import asyncio
import sys
import os

# Add the openai-mcp-client directory to the path
sys.path.insert(0, '/root/fixxitV2/openai-mcp-client')

from tool_manager import tool_manager
from openai_manager import openai_manager

async def test_dynamic_tools():
    """Test dynamic tool loading and configuration."""
    
    print("🧪 Testing Dynamic Tool Management System")
    print("=" * 60)
    
    # Test 1: Check initial tool status
    print("\n1️⃣ Testing Initial Tool Status:")
    status = tool_manager.get_tool_status()
    print(f"   📊 Total tools in registry: {status['total_tools']}")
    print(f"   ✅ Enabled tools: {status['enabled_tools']}")
    print(f"   📋 Enabled tools list: {', '.join(status['enabled_list'])}")
    
    # Test 2: Check function definitions generation
    print("\n2️⃣ Testing Function Definitions Generation:")
    functions = tool_manager.get_enabled_functions()
    print(f"   🔧 Generated {len(functions)} function definitions")
    for func in functions:
        func_name = func['function']['name']
        desc = func['function']['description'][:60] + "..." if len(func['function']['description']) > 60 else func['function']['description']
        print(f"   - {func_name}: {desc}")
    
    # Test 3: Check mappings
    print("\n3️⃣ Testing Tool Mappings:")
    mcp_mapping = tool_manager.get_mcp_mapping()
    print(f"   🔗 Function to MCP mappings:")
    for func_name, mcp_name in mcp_mapping.items():
        print(f"   - {func_name} → {mcp_name if mcp_name else 'CLIENT_HANDLED'}")
    
    # Test 4: Test with disabled tool
    print("\n4️⃣ Testing Tool Disabling:")
    print("   📝 Current tool_config.env settings:")
    
    # Read current config
    config_path = "/root/fixxitV2/tool_config.env"
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    enabled_tools = []
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.strip().split('=', 1)
            if value.lower() == 'true':
                enabled_tools.append(key)
    
    print(f"   ✅ Enabled in config: {', '.join(enabled_tools)}")
    
    # Test 5: Test AI Integration
    print("\n5️⃣ Testing AI Integration:")
    try:
        if not await openai_manager.initialize():
            print("   ❌ Failed to initialize AI manager")
            return
        
        print("   ✅ AI manager initialized successfully")
        
        # Test a simple query
        print("   🤖 Testing AI query with dynamic tools...")
        response = await openai_manager.process_user_message("What machines are currently down?")
        
        print("   📝 AI Response:")
        # Truncate long responses for readability
        response_preview = response[:200] + "..." if len(response) > 200 else response
        print(f"   {response_preview}")
        
        await openai_manager.shutdown()
        
    except Exception as e:
        print(f"   ❌ Error testing AI integration: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 Dynamic Tool Management Test Complete!")

async def test_tool_configuration_changes():
    """Test changing tool configuration at runtime."""
    
    print("\n🔄 Testing Configuration Changes:")
    print("-" * 40)
    
    # Show current status
    status = tool_manager.get_tool_status()
    print(f"Current enabled tools: {status['enabled_tools']}")
    
    # Try to simulate a config change (just for testing)
    print("📝 Configuration changes would normally be done by editing tool_config.env")
    print("   Example: TOOL_PARTS_INVENTORY=false  # to disable parts inventory")
    print("   Then call: tool_manager.reload_config()")
    

if __name__ == "__main__":
    asyncio.run(test_dynamic_tools())
    asyncio.run(test_tool_configuration_changes())