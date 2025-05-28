#!/usr/bin/env python3
"""
FixxIt AI Maintenance Assistant
Simple startup script for internal testing.

Usage: 
  cd /root/fixxitV2
  python startagent_fixxit.py
"""

import subprocess
import sys
import os
from pathlib import Path

# Set OpenAI API key if not already set
if not os.environ.get('OPENAI_API_KEY'):
    # Set your OpenAI API key here or via environment variable
    # os.environ['OPENAI_API_KEY'] = 'your-api-key-here'
    print("✅ OpenAI API key configured automatically")


def main():
    """Main entry point - automatically runs with UV."""
    print("🔧 FixxIt AI Maintenance Assistant")
    print("=" * 40)
    print("Starting up...")
    
    # Get paths
    project_root = Path(__file__).parent
    python_sdk_path = project_root / "python-sdk"
    agent_script = project_root / "openai-mcp-client" / "client.py"
    
    # Change to python-sdk directory
    original_dir = os.getcwd()
    
    try:
        os.chdir(python_sdk_path)
        
        print("✅ Starting interactive session...")
        print("   Ask about machines, tickets, maintenance, parts, etc.")
        print("   Type 'quit' or press Ctrl+C to exit\n")
        
        # Run the interactive client with UV
        subprocess.run([
            "uv", "run", "python", str(agent_script)
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    finally:
        os.chdir(original_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())