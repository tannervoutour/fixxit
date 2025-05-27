# MCP SQLite Maintenance Server

A Model Context Protocol (MCP) server that provides AI agents with access to a machine maintenance database through standardized tools and resources.

## Overview

This server exposes a SQLite database containing machine maintenance data through the MCP protocol, allowing AI assistants to help with:

- **Machine Troubleshooting** - Find machines by location, status, or model
- **Ticket Management** - Search and filter trouble tickets by priority and status  
- **Maintenance History** - Access maintenance records and technician assignments
- **Parts Inventory** - Search parts and check stock levels
- **Fault Code Lookup** - Get troubleshooting steps for error codes
- **Database Inspection** - View schema, statistics, and relationships

## Features

### 🔧 MCP Tools (AI Actions)
- `execute_sql_query` - Run custom SELECT queries (read-only)
- `find_machines` - Search machines by location, status, model, manufacturer
- `get_tickets` - Filter trouble tickets by status, priority, machine
- `get_maintenance_records` - View maintenance history with filtering
- `find_parts` - Search parts inventory and check stock levels
- `lookup_fault_code` - Get fault code details and troubleshooting steps
- `get_technician_details` - View technician info and expertise areas

### 📋 MCP Resources (AI Data)
- `schema://tables` - Complete database schema information
- `data://table/{name}` - Sample data from specific tables
- `stats://database` - Real-time database statistics and health
- `relationships://tables` - Foreign key relationships between tables
- `overview://maintenance` - High-level maintenance system status

### 🛡️ Security Features
- **Read-only access** - Only SELECT queries allowed
- **Query validation** - Prevents SQL injection and dangerous operations
- **Table restrictions** - Access limited to maintenance tables only
- **Result limits** - Configurable limits on query results

## Database Schema

The maintenance database includes:

- **machines** - Equipment inventory with location and status
- **technicians** - Staff information with expertise areas
- **fault_codes** - Error definitions with troubleshooting steps
- **maintenance_records** - Service history and work performed
- **trouble_tickets** - Issue tracking and resolution
- **parts_inventory** - Spare parts with stock levels and compatibility

## Installation

1. **Clone/copy this directory** to your local machine

2. **Install dependencies** (if using outside the main python-sdk):
   ```bash
   pip install mcp[cli]
   ```

3. **Run the server**:
   ```bash
   python server.py
   ```

## Testing with MCP Inspector

Test the server using the MCP development tools:

```bash
# From the main python-sdk directory
uv run mcp dev /path/to/mcp-sqlite-server/server.py
```

This opens the MCP Inspector web interface where you can:
- Test all available tools
- Browse resources  
- Execute sample queries
- View the database schema

## Usage Examples

### Finding Machines
```python
# Search for machines in Building A
find_machines(location="Building A")

# Find all machines that are down
find_machines(status="down")

# Search by manufacturer
find_machines(manufacturer="Haas")
```

### Trouble Tickets
```python
# Get all urgent open tickets
get_tickets(priority="urgent", status="open")

# Get tickets for a specific machine
get_tickets(machine_id=5)
```

### Maintenance History  
```python
# Get recent maintenance for a machine
get_maintenance_records(machine_id=1, days_back=30)

# Find all emergency repairs
get_maintenance_records(maintenance_type="emergency")
```

### Parts Search
```python
# Find parts for a specific model
find_parts(compatible_model="CNC-X200")

# Check low stock items
find_parts(low_stock_only=True)
```

### Custom Queries
```python
# Complex query with joins
execute_sql_query('''
    SELECT m.serial_number, m.location, t.description, t.priority
    FROM machines m
    JOIN trouble_tickets t ON m.id = t.machine_id  
    WHERE t.status = 'open'
    ORDER BY t.priority DESC
''')
```

## Configuration

Edit `config.py` to customize:

- **Database path** - Location of SQLite database file
- **Query limits** - Maximum results per query
- **Security settings** - Enable/disable custom queries
- **Connection settings** - Timeouts and performance tuning

## Architecture

```
AI Agent (GPT-4o, Claude, etc.)
    ↓
MCP Client (Your wrapper)  
    ↓
MCP Protocol
    ↓
FastMCP Server (this project)
    ↓
SQLite Database (maintenance data)
```

## Mock Data

The server includes realistic mock data for testing:

- **8 machines** across multiple buildings and manufacturers
- **5 technicians** with different expertise levels
- **8 fault codes** with troubleshooting procedures  
- **Multiple maintenance records** and trouble tickets
- **Parts inventory** with stock tracking

## Next Steps

This server is designed as **Phase 1** of a larger system. Future phases will include:

- **Phase 2**: OpenAI wrapper client for GPT-4o integration
- **Phase 3**: MCP client bridge and conversation management
- **Phase 4**: Enhanced error handling and authentication
- **Phase 5**: Production deployment and monitoring

## License

This project is part of the MCP Python SDK and follows the same MIT license.