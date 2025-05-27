"""Main MCP server for SQLite maintenance database access."""

import sys
import os

# Add the parent directory to Python path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from config import config
from tools.query_tools import (
    execute_query,
    search_machines,
    get_trouble_tickets,
    get_maintenance_history,
    search_parts
)
from tools.schema_tools import (
    get_database_schema,
    get_table_info,
    get_database_statistics,
    get_fault_code_info,
    get_technician_info
)
from resources.database_resources import (
    get_schema_resource,
    get_table_data_resource,
    get_database_stats_resource,
    get_relationships_resource,
    get_maintenance_overview_resource
)

# Create the FastMCP server
mcp = FastMCP(
    name=config.SERVER_NAME,
    dependencies=["sqlite3"]  # Built-in to Python
)


# === MCP TOOLS ===
# Tools allow the AI to perform actions and execute queries

@mcp.tool()
def execute_sql_query(query: str, limit: int = 100) -> str:
    """
    Execute a SELECT query against the maintenance database.
    
    Args:
        query: SQL SELECT query to execute (only SELECT statements allowed)
        limit: Maximum number of rows to return (default 100, max 1000)
    
    Returns:
        JSON string with query results or error message
    """
    return execute_query(query, limit)


@mcp.tool()
def find_machines(
    location: str = None,
    status: str = None,
    model: str = None,
    manufacturer: str = None
) -> str:
    """
    Search for machines based on various criteria.
    
    Args:
        location: Filter by machine location (partial match)
        status: Filter by status (operational, maintenance, down, retired)
        model: Filter by machine model (partial match)
        manufacturer: Filter by manufacturer (partial match)
    
    Returns:
        JSON string with matching machines
    """
    return search_machines(location, status, model, manufacturer)


@mcp.tool()
def get_tickets(
    status: str = None,
    priority: str = None,
    machine_id: int = None,
    limit: int = 50
) -> str:
    """
    Get trouble tickets with optional filtering.
    
    Args:
        status: Filter by status (open, assigned, in_progress, resolved, closed)
        priority: Filter by priority (low, medium, high, urgent)
        machine_id: Filter by specific machine ID
        limit: Maximum number of tickets to return
    
    Returns:
        JSON string with trouble tickets
    """
    return get_trouble_tickets(status, priority, machine_id, limit)


@mcp.tool()
def get_maintenance_records(
    machine_id: int = None,
    technician_id: int = None,
    maintenance_type: str = None,
    days_back: int = 30
) -> str:
    """
    Get maintenance history records with filtering.
    
    Args:
        machine_id: Filter by specific machine ID
        technician_id: Filter by specific technician ID
        maintenance_type: Filter by type (preventive, corrective, emergency, inspection)
        days_back: How many days back to look (default 30)
    
    Returns:
        JSON string with maintenance records
    """
    return get_maintenance_history(machine_id, technician_id, maintenance_type, days_back)


@mcp.tool()
def find_parts(
    part_number: str = None,
    name: str = None,
    compatible_model: str = None,
    low_stock_only: bool = False
) -> str:
    """
    Search parts inventory with various filters.
    
    Args:
        part_number: Search by part number (partial match)
        name: Search by part name (partial match)
        compatible_model: Search by compatible machine model
        low_stock_only: Show only parts below minimum stock level
    
    Returns:
        JSON string with parts search results
    """
    return search_parts(part_number, name, compatible_model, low_stock_only)


@mcp.tool()
def get_schema() -> str:
    """
    Get complete database schema information.
    
    Returns:
        JSON string with all table schemas and structures
    """
    return get_database_schema()


@mcp.tool()
def inspect_table(table_name: str) -> str:
    """
    Get detailed information about a specific table.
    
    Args:
        table_name: Name of the table to inspect
    
    Returns:
        JSON string with table structure and sample data
    """
    return get_table_info(table_name)


@mcp.tool()
def get_stats() -> str:
    """
    Get comprehensive database statistics and metrics.
    
    Returns:
        JSON string with database statistics
    """
    return get_database_statistics()


@mcp.tool()
def lookup_fault_code(fault_code: str = None) -> str:
    """
    Get fault code information for troubleshooting.
    
    Args:
        fault_code: Specific fault code to look up (if None, returns all codes)
    
    Returns:
        JSON string with fault code details and troubleshooting steps
    """
    return get_fault_code_info(fault_code)


@mcp.tool()
def get_technician_details(technician_id: int = None) -> str:
    """
    Get technician information and expertise areas.
    
    Args:
        technician_id: Specific technician ID (if None, returns all technicians)
    
    Returns:
        JSON string with technician details and recent work stats
    """
    return get_technician_info(technician_id)


# === MCP RESOURCES ===
# Resources provide data that can be read by the AI

@mcp.resource("schema://tables")
def schema_resource() -> str:
    """Database schema information for all tables."""
    return get_schema_resource()


@mcp.resource("data://table/{table_name}")
def table_data_resource(table_name: str) -> str:
    """Sample data from a specific table."""
    return get_table_data_resource(table_name)


@mcp.resource("stats://database")
def database_stats_resource() -> str:
    """Database statistics and health information."""
    return get_database_stats_resource()


@mcp.resource("relationships://tables")
def relationships_resource() -> str:
    """Table relationships and foreign key information."""
    return get_relationships_resource()


@mcp.resource("overview://maintenance")
def maintenance_overview_resource() -> str:
    """High-level maintenance system overview."""
    return get_maintenance_overview_resource()


# === SERVER STARTUP ===

if __name__ == "__main__":
    # Initialize database on startup
    from utils.db_connection import db_manager
    
    # Ensure database exists and is populated
    try:
        stats = db_manager.get_database_stats()
        print(f"✅ Database initialized with {stats['total_tables']} tables")
        for table_name, table_info in stats['table_stats'].items():
            print(f"   📊 {table_name}: {table_info['row_count']} rows")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Run the MCP server
    print(f"🚀 Starting {config.SERVER_NAME} v{config.SERVER_VERSION}")
    print(f"📁 Database: {config.get_database_path()}")
    print("🔧 Available tools: execute_sql_query, find_machines, get_tickets, get_maintenance_records, find_parts, lookup_fault_code, get_technician_details")
    print("📋 Available resources: schema://tables, data://table/{name}, stats://database, relationships://tables, overview://maintenance")
    
    mcp.run()