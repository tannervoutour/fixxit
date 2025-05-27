"""Test conversation context with multiple turns."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from openai_manager import openai_manager


async def test_conversation_flow():
    """Test multi-turn conversation with context."""
    
    # Initialize the system
    print("🚀 Initializing OpenAI MCP client...")
    success = await openai_manager.initialize()
    if not success:
        print("❌ Failed to initialize")
        return
    
    print("✅ Client ready! Testing conversation flow...\n")
    
    # Test conversation sequence
    conversation = [
        "What machines are currently down?",
        "What's wrong with it?", 
        "How do I fix that problem?",
        "Do we have the parts needed?"
    ]
    
    for i, query in enumerate(conversation, 1):
        print(f"🗣️  Turn {i}: {query}")
        print("-" * 50)
        
        response = await openai_manager.process_user_message(query)
        print(f"🤖 Assistant: {response}\n")
        
        # Show context after each turn
        from conversation_manager import conversation_manager
        context = conversation_manager.get_conversation_summary()
        print(f"🧠 Context: {context}\n")
        print("=" * 70)
        
        # Small delay between turns
        await asyncio.sleep(1)
    
    # Cleanup
    await openai_manager.shutdown()
    print("🎯 Conversation test complete!")


if __name__ == "__main__":
    asyncio.run(test_conversation_flow())