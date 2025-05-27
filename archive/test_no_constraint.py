#!/usr/bin/env python3
"""Test script for the new no-constraint system."""

import asyncio
import sys
import os

# Add the openai-mcp-client directory to the path
sys.path.insert(0, '/root/fixxitV2/openai-mcp-client')

from openai_manager import openai_manager

async def test_query(query: str):
    """Test a single query with the new system."""
    try:
        print(f"🧪 Testing query: {query}")
        print("=" * 50)
        
        # Initialize the OpenAI manager
        if not await openai_manager.initialize():
            print("❌ Failed to initialize")
            return
        
        # Process the query
        response = await openai_manager.process_user_message(query)
        
        print("🤖 AI Response:")
        print(response)
        
        # Shutdown
        await openai_manager.shutdown()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run the test."""
    test_queries = [
        "What error codes are associated with CONV-B100?",
        "What machines are currently down?",
        "Show me urgent tickets"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        await test_query(query)
        print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())