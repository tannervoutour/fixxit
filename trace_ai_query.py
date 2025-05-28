#!/usr/bin/env python3
"""
Trace an AI query to see exactly what's happening step by step.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Set API key
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

# Add path
sys.path.insert(0, str(Path(__file__).parent / "openai-mcp-client"))

async def trace_query():
    """Trace a specific query through the AI system."""
    
    print("🧪 TRACING AI QUERY PROCESSING")
    print("=" * 60)
    
    try:
        # Import components
        from openai_manager import OpenAIManager
        from mcp_bridge import MCPBridge
        from tool_manager import ToolManager
        
        # Initialize components
        print("🔧 Initializing AI components...")
        
        tool_manager = ToolManager()
        enabled_tools = tool_manager.get_enabled_tool_configs()
        print(f"✅ Tool Manager: {len(enabled_tools)} tools enabled")
        
        # Show which tools are available
        print("📋 Available tools:")
        for tool_name, tool_info in enabled_tools.items():
            print(f"   - {tool_name}: {tool_info['description'][:60]}...")
        
        # Initialize OpenAI manager with tool manager
        openai_manager = OpenAIManager(tool_manager, None)  # We'll mock the MCP bridge
        
        print(f"\n🤖 Testing with sample query...")
        
        # Test query
        query = "What safety procedures are documented for the PowerPress machine?"
        print(f"Query: {query}")
        
        # Unfortunately, we can't easily trace the full AI without the async infrastructure
        # But we can analyze the tool definitions the AI receives
        
        print(f"\n📋 Function definitions AI receives:")
        function_defs = tool_manager.generate_openai_functions()
        
        for func in function_defs:
            if 'safety' in func['description'].lower() or 'procedure' in func['description'].lower():
                print(f"✅ Relevant tool: {func['name']}")
                print(f"   Description: {func['description']}")
                print(f"   Parameters: {list(func['parameters']['properties'].keys())}")
        
        print(f"\n🎯 EXPECTED AI FLOW for safety query:")
        print("1. AI should recognize this is asking about safety procedures")
        print("2. AI should identify PowerPress as the target machine") 
        print("3. AI should call search_manual_procedures(procedure_type='safety', machine_name='PowerPress')")
        print("4. OR call search_machine_docs(machine_name='PowerPress') then get_sections")
        print("5. OR call find_troubleshooting('safety PowerPress')")
        print("6. AI should get relevant safety sections and return page references")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This indicates an issue with the Python module structure")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_tool_descriptions():
    """Analyze if tool descriptions are clear for AI."""
    print(f"\n🔍 TOOL DESCRIPTION ANALYSIS")
    print("=" * 60)
    
    # Check tool registry
    try:
        import yaml
        with open("/root/fixxitV2/tool_registry.yaml", 'r') as f:
            registry = yaml.safe_load(f)
        
        print("📋 Tool Registry Analysis:")
        
        safety_related_tools = []
        for tool_name, tool_info in registry['tools'].items():
            desc = tool_info['description'].lower()
            if any(word in desc for word in ['safety', 'procedure', 'search', 'troubleshoot']):
                safety_related_tools.append((tool_name, tool_info))
        
        print(f"\n🛡️ Safety-related tools ({len(safety_related_tools)}):")
        for tool_name, tool_info in safety_related_tools:
            print(f"\n   🔧 {tool_name}:")
            print(f"      Description: {tool_info['description']}")
            print(f"      MCP Function: {tool_info['mcp_function']}")
            
            # Check if parameters are clear
            params = tool_info.get('parameters', {})
            required_params = [name for name, info in params.items() if info.get('required', False)]
            optional_params = [name for name, info in params.items() if not info.get('required', False)]
            
            if required_params:
                print(f"      Required params: {required_params}")
            if optional_params:
                print(f"      Optional params: {optional_params}")
        
        # Check tool configuration
        print(f"\n⚙️ Tool Configuration Check:")
        with open("/root/fixxitV2/tool_config.env", 'r') as f:
            config = f.read()
        
        enabled_tools = [line.split('=')[0] for line in config.split('\n') if '=true' in line]
        disabled_tools = [line.split('=')[0] for line in config.split('\n') if '=false' in line]
        
        print(f"   Enabled tools: {len(enabled_tools)}")
        print(f"   Disabled tools: {len(disabled_tools)}")
        
        # Check if key tools are enabled
        key_tools = ['TOOL_MANUAL_SECTIONS', 'TOOL_PROCEDURES', 'TOOL_TROUBLESHOOTING']
        for tool in key_tools:
            status = "✅ ENABLED" if f"{tool}=true" in config else "❌ DISABLED"
            print(f"   {tool}: {status}")
            
    except Exception as e:
        print(f"❌ Tool analysis failed: {e}")

def suggest_improvements():
    """Suggest specific improvements based on analysis."""
    print(f"\n💡 SPECIFIC IMPROVEMENT SUGGESTIONS")
    print("=" * 60)
    
    print("Based on the analysis, here are potential issues and fixes:")
    print()
    
    print("1. 🎯 **Tool Selection Issues:**")
    print("   Problem: AI might not know which tool to use for safety queries")
    print("   Fix: Improve tool descriptions to be more specific")
    print("   Example: 'search_manual_procedures' should clearly state it finds safety procedures")
    print()
    
    print("2. 🔄 **Tool Chaining Issues:**")
    print("   Problem: AI might not chain tools effectively")
    print("   Fix: Add examples in tool descriptions showing multi-step usage")
    print("   Example: 'First search machine, then get sections, then get content'")
    print()
    
    print("3. 📝 **Response Formation Issues:**")
    print("   Problem: AI might find data but not format it well for user")
    print("   Fix: Improve system prompt to emphasize page references and clear formatting")
    print()
    
    print("4. 🔍 **Search Strategy Issues:**")
    print("   Problem: AI might use wrong search terms or approach")
    print("   Fix: Add keywords and examples to tool descriptions")
    print("   Example: 'Use this for safety, operation, maintenance, troubleshooting procedures'")

async def main():
    """Run complete trace analysis."""
    await trace_query()
    analyze_tool_descriptions()
    suggest_improvements()
    
    print(f"\n🎯 NEXT ACTION:")
    print("Run a live test with the AI to see which tools it actually calls")
    print("Compare with expected tool usage from analysis above")

if __name__ == "__main__":
    asyncio.run(main())