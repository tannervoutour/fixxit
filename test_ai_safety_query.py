#!/usr/bin/env python3
"""
Test AI safety query processing with detailed logging.
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

async def test_safety_query():
    """Test a safety query and log exactly what happens."""
    
    print("🧪 AI SAFETY QUERY TEST")
    print("=" * 60)
    
    try:
        # Import components
        from openai_manager import OpenAIManager
        
        # Initialize OpenAI manager (this handles all components)
        print("🔧 Initializing OpenAI manager...")
        openai_mgr = OpenAIManager()
        await openai_mgr.initialize()
        
        # Test query
        query = "What safety procedures are documented for the PowerPress machine?"
        print(f"📝 Query: {query}")
        print()
        
        # Process query with detailed logging
        print("🤖 Processing query...")
        response = await openai_mgr.process_user_message(query)
        
        print("🎯 AI Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        # Analyze the response
        print("\n📊 RESPONSE ANALYSIS:")
        
        # Check if response contains page references
        has_page_refs = any(word in response.lower() for word in ['page', 'p.', 'pp.', 'section'])
        print(f"✅ Contains page references: {has_page_refs}")
        
        # Check if response mentions safety procedures
        has_safety_info = any(word in response.lower() for word in ['safety', 'procedure', 'warning', 'caution'])
        print(f"✅ Contains safety information: {has_safety_info}")
        
        # Check if response mentions PowerPress
        mentions_powerpress = 'powerpress' in response.lower()
        print(f"✅ Mentions PowerPress machine: {mentions_powerpress}")
        
        print(f"\n🎯 QUERY SUCCESS SCORE:")
        score = sum([has_page_refs, has_safety_info, mentions_powerpress])
        print(f"Score: {score}/3 - {'✅ SUCCESS' if score >= 2 else '❌ NEEDS IMPROVEMENT'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_multiple_queries():
    """Test multiple different queries to see patterns."""
    
    print(f"\n🧪 MULTIPLE QUERY PATTERN TEST")
    print("=" * 60)
    
    test_queries = [
        "What safety procedures are documented for the PowerPress machine?",
        "How do I troubleshoot PowerPress machine issues?", 
        "Show me operating procedures for Line 1 machines",
        "What maintenance is required for the Feeder machine?",
        "Are there any safety warnings for CSP machines?"
    ]
    
    try:
        from openai_manager import OpenAIManager
        openai_mgr = OpenAIManager()
        await openai_mgr.initialize()
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test Query {i}: {query}")
            
            try:
                response = await openai_mgr.process_user_message(query)
                
                # Quick analysis
                has_page_refs = any(word in response.lower() for word in ['page', 'p.', 'pp.', 'section'])
                has_specific_info = len(response) > 100  # Non-trivial response
                
                print(f"   Response length: {len(response)} chars")
                print(f"   Has page refs: {'✅' if has_page_refs else '❌'}")
                print(f"   Has content: {'✅' if has_specific_info else '❌'}")
                
                if len(response) < 200:  # Show short responses in full
                    print(f"   Response: {response[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Setup error: {e}")

def analyze_expected_vs_actual():
    """Compare what should happen vs what actually happens."""
    
    print(f"\n🎯 EXPECTED VS ACTUAL ANALYSIS")
    print("=" * 60)
    
    print("📋 EXPECTED AI FLOW for 'PowerPress safety procedures':")
    print("1. AI should recognize this asks about safety procedures for PowerPress")
    print("2. AI should call search_manual_procedures(procedure_type='safety', machine_name='PowerPress')")
    print("3. OR AI should call find_troubleshooting(search_query='safety PowerPress')")  
    print("4. OR AI should call search_machine_docs(machine_name='PowerPress') then get_sections")
    print("5. AI should get section content and provide page references")
    print()
    
    print("🤔 POSSIBLE FAILURE POINTS:")
    print("A. Tool Selection: AI chooses wrong tool or no tool")
    print("B. Parameter Usage: AI uses wrong parameters (e.g., wrong procedure_type)")
    print("C. Tool Chaining: AI doesn't follow up with get_section_text")
    print("D. Response Formation: AI finds data but doesn't format it well")
    print("E. Search Terms: AI uses poor search terms that don't match content")
    print()
    
    print("🔍 DEBUGGING STRATEGY:")
    print("1. Check which tools AI actually calls (logs should show this)")
    print("2. Check what parameters AI uses (are they correct?)")
    print("3. Check what data tools return (is relevant data available?)")
    print("4. Check how AI formats final response (does it include page refs?)")

async def main():
    """Run complete safety query test."""
    await test_safety_query()
    await test_multiple_queries() 
    analyze_expected_vs_actual()
    
    print(f"\n💡 NEXT STEPS:")
    print("1. Check logs from conversation_manager to see actual tool calls")
    print("2. If tools aren't being called, improve tool descriptions")
    print("3. If wrong tools called, adjust tool selection logic")
    print("4. If right tools called but wrong params, improve parameter descriptions")
    print("5. If data found but poorly formatted, improve response generation")

if __name__ == "__main__":
    asyncio.run(main())