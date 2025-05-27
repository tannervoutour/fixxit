"""Example troubleshooting conversation flow."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from client import MaintenanceAssistant


async def run_troubleshooting_example():
    """Simulate a troubleshooting conversation with context."""
    assistant = MaintenanceAssistant()
    
    if not await assistant.initialize():
        print("Failed to initialize assistant")
        return
    
    # Simulate a realistic troubleshooting flow
    conversation_flow = [
        "What machines are currently having issues?",
        "Tell me more about that welding robot problem",
        "What's the fault code W001 mean?", 
        "Do we have the parts needed to fix this?",
        "Who should I assign to handle this repair?",
        "Show me the maintenance history for that machine"
    ]
    
    print("🔧 Simulating troubleshooting conversation...")
    print("=" * 50)
    
    for i, query in enumerate(conversation_flow, 1):
        print(f"\\n[Turn {i}] User: {query}")
        print("-" * 40)
        
        response = await assistant.openai_manager.process_user_message(query)
        print(f"Assistant: {response}")
        
        # Show context after each turn
        context = assistant.openai_manager.conversation_manager.get_conversation_summary()
        if context != "No active context":
            print(f"\\n🧠 Context: {context}")
        
        # Wait between turns
        await asyncio.sleep(2)
    
    print("\\n" + "=" * 50)
    print("🎯 Troubleshooting conversation complete!")
    print("Notice how the assistant maintained context throughout the conversation.")
    
    await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(run_troubleshooting_example())