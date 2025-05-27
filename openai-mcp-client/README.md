# OpenAI MCP Maintenance Client

A conversational AI assistant that connects OpenAI's GPT-4o to a maintenance database through the Model Context Protocol (MCP). This client enables natural language interactions with machine maintenance data.

## Overview

This Phase 2 component bridges OpenAI's API with the MCP SQLite server from Phase 1, creating a conversational AI that can:

- **Answer natural language questions** about machines, tickets, and maintenance
- **Maintain conversation context** across multiple turns
- **Handle follow-up questions** using remembered entities
- **Call appropriate database functions** based on user intent
- **Format results** in human-readable format

## Architecture

```
User Question → OpenAI Client → GPT-4o → Function Calls → MCP Bridge → SQLite Server
     ↑                                                              ↓
User Response ← Formatted Results ← GPT-4o ← Function Results ← MCP Bridge ← Database
```

## Features

### 🧠 **Conversational Intelligence**
- **Context Memory**: Remembers machines, tickets, technicians from previous turns
- **Reference Resolution**: Understands "that machine", "the urgent ticket", etc.
- **Intent Recognition**: Detects troubleshooting, maintenance, parts management
- **Smart Defaults**: Auto-fills parameters based on conversation context

### 🔧 **Natural Language Interface**
- **Ask about machines**: "What machines are down in Building A?"
- **Check trouble tickets**: "Show me urgent tickets for the welding robot"
- **Maintenance history**: "When was the CNC machine last serviced?"
- **Parts inventory**: "Do we have the parts to fix fault code E001?"
- **Technician lookup**: "Who's our hydraulics expert?"

### 📊 **Rich Formatting**
- **Structured responses** with emojis and clear organization
- **Priority highlighting** for urgent issues
- **Actionable suggestions** for next steps
- **Error handling** with helpful guidance

## Installation

### Prerequisites
- Python 3.8+ 
- OpenAI API key
- MCP SQLite server running (from Phase 1)

### Setup
1. **Ensure MCP server is working**:
   ```bash
   cd /root/fixxitV2/python-sdk
   uv run mcp dev ../mcp-sqlite-server/server.py
   ```

2. **Install dependencies** (already done in main project):
   ```bash
   cd /root/fixxitV2/python-sdk
   uv add openai python-dotenv pydantic rich
   ```

3. **Configure API key** (already set in config.py):
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Usage

### Interactive Mode
```bash
cd /root/fixxitV2/python-sdk
uv run python ../openai-mcp-client/client.py
```

### Single Query Mode
```bash
cd /root/fixxitV2/python-sdk
uv run python ../openai-mcp-client/client.py "Show me all machines that are down"
```

### Example Session
```
🔧 AI Maintenance Assistant
===============================

You: What machines are currently down?

🤖 Assistant:
┌─────────────────────────────────────┐
│ Found 1 machine that's currently    │
│ down:                               │
│                                     │
│ ❌ WELD-R300 (SN005678)            │
│    📍 Building C - Assembly         │
│    🏭 Robotic Welding Corp          │
│    📊 Status: down                  │
│    🗓️ Next Maintenance: 2024-06-01 │
└─────────────────────────────────────┘

You: What's wrong with it?

🤖 Assistant:
┌─────────────────────────────────────┐
│ 🚨 ⚙️ Ticket #4 - URGENT           │
│    🏭 Machine: WELD-R300 (SN005678) │
│    📍 Location: Building C - Assembly│
│    👤 Reported by: Operator Brown   │
│    🔍 Fault Code: W001              │
│    📝 Issue: Welding robot producing│
│    poor quality welds, arc keeps    │
│    breaking                         │
│    🔧 Assigned to: Mike Johnson     │
└─────────────────────────────────────┘

You: How do I fix W001?

🤖 Assistant:
┌─────────────────────────────────────┐
│ 🚨 Fault Code W001 - MEDIUM Priority│
│                                     │
│ 🏭 Machine Model: WELD-R300         │
│ 📝 Description: Arc instability     │
│ ⏱️ Estimated Repair Time: 40 minutes│
│                                     │
│ 🔧 Troubleshooting Steps:           │
│ 1. Check gas flow                   │
│ 2. Inspect wire feed                │
│ 3. Clean contact tips               │
│ 4. Verify ground connection         │
└─────────────────────────────────────┘
```

## Available Functions

The assistant can call these functions automatically based on user questions:

### **Equipment Management**
- `search_equipment` - Find machines by location, status, model
- `get_maintenance_tickets` - Retrieve trouble tickets  
- `get_service_history` - View maintenance records

### **Parts & Inventory**
- `search_parts_inventory` - Find parts and check stock
- `get_troubleshooting_help` - Lookup fault codes

### **People & Expertise**
- `get_technician_info` - Find technicians and their skills
- `get_database_overview` - System health dashboard

### **Advanced Queries**
- `query_maintenance_database` - Custom SQL for complex requests

## Conversation Context

The assistant maintains intelligent context:

### **Entity Tracking**
```python
# Remembers from conversation:
entities = {
    "machine_5": {
        "type": "machine", 
        "id": 5,
        "name": "WELD-R300",
        "last_mentioned": 3
    },
    "ticket_4": {
        "type": "ticket",
        "id": 4, 
        "priority": "urgent",
        "last_mentioned": 2
    }
}
```

### **Reference Resolution**
- **"that machine"** → Uses machine_id from context
- **"the urgent ticket"** → Finds highest priority ticket
- **"check its history"** → Uses current focused machine
- **"who's assigned?"** → Uses technician from current ticket

### **Smart Context**
- **Location awareness**: "Building A" remembered for follow-ups
- **Priority filtering**: "urgent" applied to subsequent queries  
- **Intent persistence**: Troubleshooting focus maintained

## Configuration

Edit `config.py` to customize:

```python
# OpenAI settings
OPENAI_MODEL = "gpt-4o"
MAX_TOKENS = 4000
TEMPERATURE = 0.1  # Low for factual responses

# Conversation settings  
MAX_CONVERSATION_HISTORY = 20
CONTEXT_RETENTION_TURNS = 5

# MCP server path
MCP_SERVER_PATH = "../mcp-sqlite-server/server.py"
```

## Examples

### Machine Status Queries
```
"What machines are down?"
"Show me all CNC machines in Building A"  
"Which machines need maintenance soon?"
"Find operational conveyor belts"
```

### Trouble Ticket Management
```
"What urgent tickets do we have?"
"Show me open tickets for the welding robot"
"Who's working on high priority issues?"
"When was ticket #4 reported?"
```

### Maintenance Planning
```
"What maintenance was done last week?"
"Show me emergency repairs this month"
"Who performed the most maintenance?"
"What's the history for machine SN001234?"
```

### Parts & Inventory
```
"Do we have hydraulic fluid in stock?"
"What parts are running low?"
"Find belts compatible with conveyor systems"
"Check stock for CNC machines"
```

### Troubleshooting Assistance
```
"How do I fix error code E001?"
"What does fault code H001 mean?"
"Show me all critical fault codes"
"What are the troubleshooting steps for W001?"
```

### Expert Assignment
```
"Who can fix hydraulic problems?"
"Find our welding experts"
"Which technician should handle this?"
"Show me all senior-level staff"
```

## Testing

### Run Example Scripts
```bash
# Basic queries
cd /root/fixxitV2/python-sdk
uv run python ../openai-mcp-client/examples/basic_queries.py

# Troubleshooting conversation
uv run python ../openai-mcp-client/examples/troubleshooting_flow.py
```

### Special Commands
In interactive mode:
- `/help` - Show usage instructions
- `/status` - System status and connection info
- `/reset` - Clear conversation context
- `/history` - Show recent conversation
- `/quit` - Exit application

## Error Handling

### Common Issues
- **"Not connected to MCP server"** → Check MCP SQLite server is running
- **"Invalid OpenAI API key"** → Verify API key in config.py
- **"Function call failed"** → Check MCP server logs

### Debugging
```bash
# Check MCP server
cd /root/fixxitV2/python-sdk
uv run mcp dev ../mcp-sqlite-server/server.py

# Check logs
tail -f maintenance_assistant.log
```

## Integration with Phase 1

This client connects to the Phase 1 MCP SQLite server:

```bash
# Phase 1: MCP Server (must be running)
/root/fixxitV2/mcp-sqlite-server/server.py

# Phase 2: OpenAI Client (this project) 
/root/fixxitV2/openai-mcp-client/client.py
```

The client automatically starts the MCP server as a subprocess, so you just need to run the client.

## Next Steps

**Phase 3** will add:
- Advanced conversation management
- Multi-session support  
- Authentication and authorization
- Performance optimization
- Production deployment features

## License

This project is part of the MCP Python SDK and follows the same MIT license.