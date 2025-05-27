"""MCP resources for exposing database information through the protocol."""

import json
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection import db_manager


def get_schema_resource() -> str:
    """
    Resource: schema://tables
    Provides complete database schema information.
    
    Returns:
        JSON string with all table schemas
    """
    try:
        tables = db_manager.get_all_tables()
        schema_info = {}
        
        for table_name in tables:
            columns = db_manager.get_table_schema(table_name)
            row_count = db_manager.get_table_row_count(table_name)
            
            schema_info[table_name] = {
                "row_count": row_count,
                "columns": [
                    {
                        "name": col["name"],
                        "type": col["type"],
                        "not_null": bool(col["notnull"]),
                        "default": col["dflt_value"],
                        "primary_key": bool(col["pk"])
                    }
                    for col in columns
                ]
            }
        
        return json.dumps({
            "database_schema": schema_info,
            "table_count": len(tables),
            "description": "Complete database schema for maintenance system"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to retrieve schema: {str(e)}"
        }, indent=2)


def get_table_data_resource(table_name: str) -> str:
    """
    Resource: data://table/{table_name}
    Provides sample data from a specific table.
    
    Args:
        table_name: Name of the table to sample
        
    Returns:
        JSON string with sample table data
    """
    try:
        # Validate table access
        allowed_tables = ['machines', 'technicians', 'fault_codes', 
                         'maintenance_records', 'trouble_tickets', 'parts_inventory']
        
        if table_name not in allowed_tables:
            return json.dumps({
                "error": f"Access denied to table: {table_name}"
            }, indent=2)
        
        # Get sample data (limit to 10 rows for resources)
        query = f"SELECT * FROM {table_name} LIMIT 10"
        sample_data = db_manager.execute_query(query)
        
        # Get total row count
        total_rows = db_manager.get_table_row_count(table_name)
        
        # Get column info
        columns = db_manager.get_table_schema(table_name)
        
        return json.dumps({
            "table_name": table_name,
            "total_rows": total_rows,
            "sample_rows": len(sample_data),
            "columns": [col["name"] for col in columns],
            "sample_data": sample_data,
            "description": f"Sample data from {table_name} table"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to retrieve table data: {str(e)}",
            "table_name": table_name
        }, indent=2)


def get_database_stats_resource() -> str:
    """
    Resource: stats://database
    Provides database statistics and health information.
    
    Returns:
        JSON string with database statistics
    """
    try:
        stats = db_manager.get_database_stats()
        
        # Calculate additional metrics
        total_rows = sum(table['row_count'] for table in stats['table_stats'].values())
        
        # Get maintenance-specific insights
        maintenance_insights = {}
        
        try:
            # Recent ticket trends
            recent_tickets = db_manager.execute_query("""
                SELECT status, COUNT(*) as count 
                FROM trouble_tickets 
                WHERE date_reported >= date('now', '-7 days')
                GROUP BY status
            """)
            maintenance_insights['recent_tickets_by_status'] = {
                row['status']: row['count'] for row in recent_tickets
            }
            
            # Machine status distribution
            machine_status = db_manager.execute_query("""
                SELECT status, COUNT(*) as count 
                FROM machines 
                GROUP BY status
            """)
            maintenance_insights['machine_status_distribution'] = {
                row['status']: row['count'] for row in machine_status
            }
            
            # Low stock parts
            low_stock = db_manager.execute_query("""
                SELECT COUNT(*) as count 
                FROM parts_inventory 
                WHERE stock_quantity <= min_stock_level
            """)
            maintenance_insights['low_stock_parts_count'] = low_stock[0]['count'] if low_stock else 0
            
            # Overdue maintenance
            overdue_maintenance = db_manager.execute_query("""
                SELECT COUNT(*) as count 
                FROM machines 
                WHERE next_maintenance < date('now') AND status != 'retired'
            """)
            maintenance_insights['overdue_maintenance_count'] = overdue_maintenance[0]['count'] if overdue_maintenance else 0
            
        except Exception as insight_error:
            maintenance_insights['error'] = f"Could not calculate insights: {str(insight_error)}"
        
        enhanced_stats = {
            **stats,
            "total_rows": total_rows,
            "maintenance_insights": maintenance_insights,
            "last_updated": "real-time"
        }
        
        return json.dumps({
            "database_statistics": enhanced_stats,
            "description": "Real-time database statistics and maintenance insights"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to retrieve database statistics: {str(e)}"
        }, indent=2)


def get_relationships_resource() -> str:
    """
    Resource: relationships://tables
    Provides information about foreign key relationships between tables.
    
    Returns:
        JSON string with table relationships
    """
    try:
        tables = db_manager.get_all_tables()
        relationships = {}
        
        for table_name in tables:
            # Get foreign keys for this table
            foreign_keys = db_manager.execute_query(f"PRAGMA foreign_key_list({table_name})")
            
            if foreign_keys:
                relationships[table_name] = {
                    "foreign_keys": [
                        {
                            "column": fk["from"],
                            "references_table": fk["table"],
                            "references_column": fk["to"]
                        }
                        for fk in foreign_keys
                    ]
                }
        
        # Add logical relationships description
        logical_relationships = {
            "machines": "Central entity - referenced by maintenance_records and trouble_tickets",
            "technicians": "Referenced by maintenance_records and trouble_tickets (assigned_technician_id)",
            "fault_codes": "Referenced by trouble_tickets for error classification",
            "maintenance_records": "Links machines and technicians with work performed",
            "trouble_tickets": "Links machines with reported issues, may reference fault_codes",
            "parts_inventory": "Standalone table, but parts_used in maintenance_records references part_number"
        }
        
        return json.dumps({
            "foreign_key_relationships": relationships,
            "logical_relationships": logical_relationships,
            "description": "Database table relationships and foreign key constraints"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to retrieve relationships: {str(e)}"
        }, indent=2)


def get_maintenance_overview_resource() -> str:
    """
    Resource: overview://maintenance
    Provides a high-level overview of maintenance system status.
    
    Returns:
        JSON string with maintenance overview
    """
    try:
        overview = {}
        
        # Machine summary
        machine_summary = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_machines,
                SUM(CASE WHEN status = 'operational' THEN 1 ELSE 0 END) as operational,
                SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as in_maintenance,
                SUM(CASE WHEN status = 'down' THEN 1 ELSE 0 END) as down,
                SUM(CASE WHEN next_maintenance < date('now') AND status != 'retired' THEN 1 ELSE 0 END) as overdue_maintenance
            FROM machines
        """)
        overview['machines'] = machine_summary[0] if machine_summary else {}
        
        # Ticket summary
        ticket_summary = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_tickets,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_tickets,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN priority = 'urgent' AND status NOT IN ('resolved', 'closed') THEN 1 ELSE 0 END) as urgent_open
            FROM trouble_tickets
        """)
        overview['tickets'] = ticket_summary[0] if ticket_summary else {}
        
        # Recent maintenance
        recent_maintenance = db_manager.execute_query("""
            SELECT COUNT(*) as completed_last_7_days
            FROM maintenance_records
            WHERE maintenance_date >= date('now', '-7 days') AND status = 'completed'
        """)
        overview['recent_maintenance'] = recent_maintenance[0] if recent_maintenance else {}
        
        # Parts status
        parts_status = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_parts,
                SUM(CASE WHEN stock_quantity <= min_stock_level THEN 1 ELSE 0 END) as low_stock_parts,
                SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END) as out_of_stock
            FROM parts_inventory
        """)
        overview['parts'] = parts_status[0] if parts_status else {}
        
        # Technician availability
        tech_info = db_manager.execute_query("""
            SELECT 
                COUNT(*) as total_technicians,
                SUM(CASE WHEN certification_level = 'expert' THEN 1 ELSE 0 END) as experts,
                SUM(CASE WHEN certification_level = 'lead' THEN 1 ELSE 0 END) as leads
            FROM technicians
            WHERE active = 1
        """)
        overview['technicians'] = tech_info[0] if tech_info else {}
        
        return json.dumps({
            "maintenance_overview": overview,
            "timestamp": "real-time",
            "description": "High-level overview of maintenance system status"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to retrieve maintenance overview: {str(e)}"
        }, indent=2)