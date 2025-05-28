"""Main MCP server for SQLite maintenance database access."""

import sys
import os
import json

# Add the parent directory to Python path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from config import config
from tools.documentation_tools import (
    search_machine_documentation,
    get_manual_sections,
    find_troubleshooting_info,
    get_section_content,
    search_procedures,
    get_documentation_overview
)
from tools.schema_tools import (
    get_database_schema,
    get_table_info,
    get_database_statistics
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
def search_machine_docs(
    machine_name: str = None,
    line_number: str = None,
    machine_type: str = None
) -> str:
    """
    Search for machines and their available documentation.
    
    Args:
        machine_name: Specific machine name (e.g., 'CSP', 'Feeder')
        line_number: Line designation (e.g., 'Line_1', 'Line_2')
        machine_type: Type of machine (e.g., 'separator', 'feeder', 'folder')
    
    Returns:
        JSON string with machine information and available documentation
    """
    result = search_machine_documentation(mcp, machine_name, line_number, machine_type)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_sections(
    machine_name: str = None,
    section_name: str = None,
    document_filename: str = None
) -> str:
    """
    Get available sections from machine manuals.
    
    Args:
        machine_name: Machine to search for
        section_name: Specific section name to filter by
        document_filename: Specific document filename to filter by
    
    Returns:
        JSON string with section information
    """
    result = get_manual_sections(mcp, machine_name, section_name, document_filename)
    return json.dumps(result, indent=2)


@mcp.tool()
def find_troubleshooting(
    search_query: str,
    machine_name: str = None
) -> str:
    """
    Search for troubleshooting information in documentation sections.
    
    Args:
        search_query: Search terms (error symptoms, part names, etc.)
        machine_name: Limit search to specific machine
    
    Returns:
        JSON string with matching troubleshooting sections
    """
    result = find_troubleshooting_info(mcp, search_query, machine_name)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_section_text(
    machine_name: str,
    section_name: str,
    document_filename: str = None
) -> str:
    """
    Get the full content of a specific section.
    
    Args:
        machine_name: Name of the machine
        section_name: Name of the section to retrieve
        document_filename: Specific document (optional if machine has multiple)
    
    Returns:
        JSON string with full section content
    """
    result = get_section_content(mcp, machine_name, section_name, document_filename)
    return json.dumps(result, indent=2)


@mcp.tool()
def search_manual_procedures(
    procedure_type: str,
    machine_name: str = None
) -> str:
    """
    Search for specific types of procedures across documentation.
    
    Args:
        procedure_type: Type of procedure (safety, operation, maintenance, etc.)
        machine_name: Limit search to specific machine
    
    Returns:
        JSON string with matching procedure sections
    """
    result = search_procedures(mcp, procedure_type, machine_name)
    return json.dumps(result, indent=2)


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
    Get comprehensive documentation database statistics and overview.
    
    Returns:
        JSON string with database statistics
    """
    result = get_documentation_overview(mcp)
    return json.dumps(result, indent=2)


# Note: Old maintenance tools (lookup_fault_code, get_technician_details) 
# have been replaced with documentation-focused tools above


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
    print("🔧 Available tools: search_machine_docs, get_sections, find_troubleshooting, get_section_text, search_manual_procedures, get_stats")
    print("📋 Available resources: schema://tables, data://table/{name}, stats://database, relationships://tables, overview://maintenance")
    
    mcp.run()