"""Basic query examples for the OpenAI MCP client."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from client import MaintenanceAssistant


async def run_basic_examples():
    """Run basic query examples."""
    assistant = MaintenanceAssistant()
    
    if not await assistant.initialize():
        print("Failed to initialize assistant")
        return
    
    # Example queries
    queries = [
        "Show me all machines that are down",
        "What urgent trouble tickets do we have?",
        "Find maintenance records for the last 7 days",
        "Check if we have any parts below minimum stock",
        "How do I troubleshoot fault code E001?",
        "Who are our expert-level technicians?"
    ]
    
    print("🔧 Running basic query examples...")
    print("=" * 50)
    
    for i, query in enumerate(queries, 1):
        print(f"\\n[{i}] Query: {query}")
        print("-" * 40)
        
        response = await assistant.openai_manager.process_user_message(query)
        print(response)
        
        # Wait a bit between queries
        await asyncio.sleep(1)
    
    await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(run_basic_examples())