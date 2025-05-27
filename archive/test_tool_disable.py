#!/usr/bin/env python3
"""Test tool enabling/disabling functionality."""

import asyncio
import sys
import os
from pathlib import Path

# Add the openai-mcp-client directory to the path
sys.path.insert(0, '/root/fixxitV2/openai-mcp-client')

from tool_manager import tool_manager
from openai_manager import openai_manager

async def test_tool_disable():
    """Test disabling and re-enabling tools."""
    
    print("🧪 Testing Tool Enable/Disable Functionality")
    print("=" * 60)
    
    # Step 1: Check initial state
    print("\n1️⃣ Initial State:")
    status = tool_manager.get_tool_status()
    print(f"   ✅ Enabled tools: {status['enabled_tools']}")
    print(f"   📋 Tool list: {', '.join(sorted(status['enabled_list']))}")
    
    # Step 2: Create a test config with some tools disabled
    print("\n2️⃣ Creating Test Configuration (disabling parts inventory):")
    
    config_path = Path("/root/fixxitV2/tool_config.env")
    backup_path = Path("/root/fixxitV2/tool_config.env.backup")
    
    # Backup original config
    if config_path.exists():
        with open(config_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        print("   💾 Backed up original config")
    
    # Create modified config with parts inventory disabled
    modified_config = """# Modified Test Configuration
TOOL_SEARCH_EQUIPMENT=true
TOOL_MAINTENANCE_TICKETS=true
TOOL_SERVICE_HISTORY=true
TOOL_PARTS_INVENTORY=false
TOOL_TROUBLESHOOTING=true
TOOL_TECHNICIAN_INFO=true
TOOL_DATABASE_QUERY=true
TOOL_SYSTEM_OVERVIEW=true
"""
    
    with open(config_path, 'w') as f:
        f.write(modified_config)
    print("   📝 Created test config with TOOL_PARTS_INVENTORY=false")
    
    # Step 3: Reload configuration
    print("\n3️⃣ Reloading Configuration:")
    if tool_manager.reload_config():
        print("   ✅ Configuration reloaded successfully")
        
        # Check new status
        new_status = tool_manager.get_tool_status()
        print(f"   📊 Enabled tools now: {new_status['enabled_tools']}")
        print(f"   📋 Tool list: {', '.join(sorted(new_status['enabled_list']))}")
        print(f"   ❌ Disabled tools: {', '.join(sorted(new_status['disabled_list']))}")
        
        # Verify parts inventory is disabled
        if 'search_parts_inventory' in new_status['disabled_list']:
            print("   ✅ Parts inventory successfully disabled!")
        else:
            print("   ❌ Parts inventory should be disabled but isn't")
    else:
        print("   ❌ Failed to reload configuration")
    
    # Step 4: Test AI with reduced tool set
    print("\n4️⃣ Testing AI with Reduced Tool Set:")
    try:
        if not await openai_manager.initialize():
            print("   ❌ Failed to initialize AI manager")
            return
        
        # Test a query that would normally use parts inventory
        print("   🤖 Testing query about parts (should fail gracefully)...")
        response = await openai_manager.process_user_message("Do we have hydraulic fluid in stock?")
        
        print("   📝 AI Response:")
        response_preview = response[:300] + "..." if len(response) > 300 else response
        print(f"   {response_preview}")
        
        await openai_manager.shutdown()
        
    except Exception as e:
        print(f"   ❌ Error testing AI: {e}")
    
    # Step 5: Restore original configuration
    print("\n5️⃣ Restoring Original Configuration:")
    if backup_path.exists():
        with open(backup_path, 'r') as src, open(config_path, 'w') as dst:
            dst.write(src.read())
        backup_path.unlink()  # Delete backup
        
        # Reload original config
        if tool_manager.reload_config():
            restored_status = tool_manager.get_tool_status()
            print(f"   ✅ Original config restored - {restored_status['enabled_tools']} tools enabled")
        else:
            print("   ❌ Failed to reload original configuration")
    else:
        print("   ❌ Backup file not found")
    
    print("\n" + "=" * 60)
    print("🎉 Tool Enable/Disable Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_tool_disable())