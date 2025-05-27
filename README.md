# FixxitV2 - AI-Powered Machine Documentation System

An intelligent maintenance assistant that provides AI-powered search through machine documentation with seamless MCP (Model Context Protocol) integration.

## 🏭 Overview

FixxitV2 is a comprehensive AI system designed for industrial maintenance operations, featuring:

- **Dynamic Tool Management**: Runtime tool configuration without code changes
- **Machine Documentation Search**: AI-powered search through PDFs, manuals, and technical documents
- **MCP Integration**: Seamless integration with Claude and other AI models
- **No-Constraint AI Philosophy**: Autonomous tool selection and decision making

## 🚀 Features

### Dynamic Tool Registry
- YAML-based tool configuration (`tool_registry.yaml`)
- Environment variable controls (`.env` files)
- Runtime tool enabling/disabling
- Automatic function generation for OpenAI integration

### Machine Documentation System
- PDF and text document processing
- Intelligent document classification
- Page-level search precision
- Machine-specific filtering
- Hybrid search (keyword + semantic)

### MCP Architecture
- Client-server communication
- Multiple transport protocols (stdio, HTTP, WebSocket)
- Authentication and authorization
- Real-time data streaming

## 📁 Project Structure

```
fixxitV2/
├── openai-mcp-client/          # OpenAI integration with MCP
│   ├── tool_manager.py         # Dynamic tool loading
│   ├── fixxit_client.py        # Main AI client
│   └── requirements.txt
├── database_bombzone/          # Machine documentation system
│   ├── schema.sql              # Database structure
│   ├── document_processor.py   # PDF/text processing
│   ├── search_engine.py        # Search functionality
│   └── mcp_tools.py           # MCP integration tools
├── python-sdk/                 # MCP Python SDK
├── mcp-sqlite-server/          # SQLite MCP server
├── tool_registry.yaml          # Master tool catalog
├── tool_config.env            # Tool enable/disable controls
└── startagent_fixxit.py       # System startup script
```

## 🛠️ Setup

### Prerequisites
- Python 3.10+
- SQLite 3
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:tannervoutour/fixxit.git
   cd fixxit
   ```

2. **Set up Python environment**
   ```bash
   cd python-sdk
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure tools**
   ```bash
   cp tool_config.env.example tool_config.env
   # Edit tool_config.env to enable/disable tools
   ```

4. **Initialize database**
   ```bash
   cd database_bombzone
   python process_files.py
   ```

## 🔧 Configuration

### Tool Management
Edit `tool_config.env` to control which tools are available:

```bash
# Equipment search and management
TOOL_SEARCH_EQUIPMENT=true
TOOL_UPDATE_EQUIPMENT=false

# Document search
TOOL_SEARCH_DOCUMENTS=true
TOOL_GET_DOCUMENT_CONTENT=true
```

### Environment Variables
Key configuration options:

- `OPENAI_API_KEY`: Your OpenAI API key
- `MCP_SERVER_URL`: MCP server endpoint
- `DATABASE_PATH`: Path to machine documentation database
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARN, ERROR)

## 🚀 Usage

### Start the System
```bash
python startagent_fixxit.py
```

### Example Queries
- "What machines are currently down?"
- "Show me the bearing replacement procedure for Line_2"
- "Find electrical diagrams for the power press"
- "List all maintenance tasks due this week"

## 🔍 Machine Documentation

The system processes various document types:
- **Operating Manuals**: Equipment operation procedures
- **Spare Parts**: Parts lists and diagrams
- **Diagrams**: Electrical, hydraulic, pneumatic schematics
- **Maintenance**: Preventive maintenance schedules
- **Troubleshooting**: Problem diagnosis guides

### Supported Machines
- Production Lines (Line_1, Line_2, Line_3, Line_4)
- Power Press
- Steam Tunnel
- Dryers
- Conveyor Systems
- And more...

## 🧠 AI Philosophy

FixxitV2 implements a "no-constraint" AI approach:
- **Autonomous Decision Making**: AI selects appropriate tools based on context
- **Cumulative Context**: Builds understanding through conversation
- **Dynamic Adaptation**: Adjusts behavior based on results
- **Minimal Guardrails**: Trusts AI judgment while maintaining safety

## 🛡️ Security

- Environment variable-based configuration
- No hardcoded secrets
- Secure MCP authentication
- Database access controls

## 📝 Development

### Adding New Tools
1. Define tool in `tool_registry.yaml`
2. Add environment control in `tool_config.env`
3. Implement MCP server endpoint
4. Test with dynamic loading

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is proprietary software for industrial maintenance operations.

## 🆘 Support

For technical support or questions:
- Check the documentation in `/docs`
- Review example configurations in `/examples`
- Contact the development team

---

**Built with ❤️ for industrial maintenance excellence**