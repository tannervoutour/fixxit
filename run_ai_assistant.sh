#!/bin/bash
# FixxIt AI Documentation Assistant - Startup Script
# This script sets the environment and starts the AI assistant

echo "🚀 Starting FixxIt AI Documentation Assistant"
echo "=============================================="

# Set OpenAI API Key
export OPENAI_API_KEY="your-api-key-here"

# Set other environment variables
export FIXXITV2_ROOT="/root/fixxitV2"
export MCP_DB_PATH="/root/fixxitV2/mcp-sqlite-server/database/database.db"

echo "✅ Environment configured"
echo "✅ OpenAI API Key: ${OPENAI_API_KEY:0:20}...${OPENAI_API_KEY: -10}"

# Start the AI assistant
echo ""
echo "🤖 Starting AI Documentation Assistant..."
echo "Ask questions about machine documentation, safety procedures, troubleshooting, etc."
echo ""

python3 startagent_fixxit.py "$@"