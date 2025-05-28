#!/bin/bash
# Environment Setup Script for FixxIt AI Documentation System
# This script configures the OpenAI API key and other environment variables

echo "🔧 Setting up FixxIt AI Documentation System Environment"
echo "==========================================================="

# Set OpenAI API Key
export OPENAI_API_KEY="your-api-key-here"

# Set other system variables
export FIXXITV2_ROOT="/root/fixxitV2"
export MCP_DB_PATH="/root/fixxitV2/mcp-sqlite-server/database/database.db"
export SYSTEM_NAME="FixxIt Documentation AI"
export VERSION="1.0.0"

# Verify configuration
echo "✅ Environment configured:"
echo "   OpenAI API Key: ${OPENAI_API_KEY:0:20}...${OPENAI_API_KEY: -10}"
echo "   System Root: $FIXXITV2_ROOT"
echo "   Database Path: $MCP_DB_PATH"

echo ""
echo "🚀 To start the AI assistant:"
echo "   cd /root/fixxitV2/python-sdk"
echo "   uv run python ../startagent_fixxit.py"
echo ""
echo "✅ Environment setup complete!"