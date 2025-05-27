"""MCP tools for database schema inspection and information."""

import json
from typing import Dict, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection import db_manager


def get_database_schema() -> str:
    """
    Get complete database schema information including all tables and their structures.
    
    Returns:
        JSON string with complete schema information
    """
    try:
        schema_info = {
            "database_type": "SQLite",
            "tables": {}
        }
        
        # Get all tables
        tables = db_manager.get_all_tables()
        
        for table_name in tables:
            # Get table schema
            columns = db_manager.get_table_schema(table_name)
            
            # Get row count
            row_count = db_manager.get_table_row_count(table_name)
            
            # Get foreign keys
            foreign_keys = db_manager.execute_query(f"PRAGMA foreign_key_list({table_name})")
            
            # Get indexes
            indexes = db_manager.execute_query(f"PRAGMA index_list({table_name})")
            
            schema_info["tables"][table_name] = {
                "row_count": row_count,
                "columns": columns,
                "foreign_keys": foreign_keys,
                "indexes": indexes
            }
        
        return json.dumps({
            "success": True,
            "schema": schema_info
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Schema retrieval failed: {str(e)}"
        }, indent=2)


def get_table_info(table_name: str) -> str:
    """
    Get detailed information about a specific table.
    
    Args:
        table_name: Name of the table to inspect
        
    Returns:
        JSON string with table information
    """
    try:
        # Validate table name
        if not query_validator.validate_table_access(table_name):
            return json.dumps({
                "error": f"Access denied to table: {table_name}"
            }, indent=2)
        
        # Get table schema
        columns = db_manager.get_table_schema(table_name)
        
        # Get row count
        row_count = db_manager.get_table_row_count(table_name)
        
        # Get sample data (first 5 rows)
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        sample_data = db_manager.execute_query(sample_query)
        
        # Get foreign keys
        foreign_keys = db_manager.execute_query(f"PRAGMA foreign_key_list({table_name})")
        
        # Get indexes
        indexes = db_manager.execute_query(f"PRAGMA index_list({table_name})")
        
        return json.dumps({
            "success": True,
            "table_name": table_name,
            "row_count": row_count,
            "columns": columns,
            "sample_data": sample_data,
            "foreign_keys": foreign_keys,
            "indexes": indexes
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Table info retrieval failed: {str(e)}",
            "table_name": table_name
        }, indent=2)


def get_database_statistics() -> str:
    """
    Get comprehensive database statistics and metrics.
    
    Returns:
        JSON string with database statistics
    """
    try:
        stats = db_manager.get_database_stats()
        
        # Add some additional computed statistics
        total_rows = sum(table_stats['row_count'] for table_stats in stats['table_stats'].values())
        
        # Get database file size (if accessible)
        try:
            import os
            db_size = os.path.getsize(db_manager.db_path)
        except:
            db_size = None
        
        # Calculate average rows per table
        avg_rows = total_rows / stats['total_tables'] if stats['total_tables'] > 0 else 0
        
        enhanced_stats = {
            **stats,
            "total_rows": total_rows,
            "average_rows_per_table": round(avg_rows, 2),
            "database_size_bytes": db_size
        }
        
        return json.dumps({
            "success": True,
            "statistics": enhanced_stats
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Statistics retrieval failed: {str(e)}"
        }, indent=2)


def get_fault_code_info(fault_code: Optional[str] = None) -> str:
    """
    Get fault code information for troubleshooting.
    
    Args:
        fault_code: Specific fault code to look up (optional)
        
    Returns:
        JSON string with fault code information
    """
    try:
        if fault_code:
            # Get specific fault code
            query = """
            SELECT code, machine_model, description, severity, 
                   troubleshooting_steps, estimated_repair_time
            FROM fault_codes 
            WHERE code = ?
            """
            results = db_manager.execute_query(query, (fault_code,))
            
            if not results:
                return json.dumps({
                    "error": f"Fault code '{fault_code}' not found"
                }, indent=2)
                
            return json.dumps({
                "success": True,
                "fault_code": fault_code,
                "details": results[0]
            }, indent=2)
        else:
            # Get all fault codes summary
            query = """
            SELECT code, machine_model, description, severity, estimated_repair_time
            FROM fault_codes 
            ORDER BY severity DESC, code
            """
            results = db_manager.execute_query(query)
            
            return json.dumps({
                "success": True,
                "total_codes": len(results),
                "fault_codes": results
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Fault code lookup failed: {str(e)}"
        }, indent=2)


def get_technician_info(technician_id: Optional[int] = None) -> str:
    """
    Get technician information and expertise areas.
    
    Args:
        technician_id: Specific technician ID to look up (optional)
        
    Returns:
        JSON string with technician information
    """
    try:
        if technician_id:
            # Get specific technician
            query = """
            SELECT id, name, employee_id, expertise_areas, contact_info,
                   certification_level, hire_date, active
            FROM technicians 
            WHERE id = ? AND active = 1
            """
            results = db_manager.execute_query(query, (technician_id,))
            
            if not results:
                return json.dumps({
                    "error": f"Technician with ID {technician_id} not found or inactive"
                }, indent=2)
            
            # Get their recent work
            recent_work_query = """
            SELECT COUNT(*) as total_jobs,
                   AVG(labor_hours) as avg_hours,
                   MAX(maintenance_date) as last_job_date
            FROM maintenance_records 
            WHERE technician_id = ? AND maintenance_date >= date('now', '-30 days')
            """
            work_stats = db_manager.execute_query(recent_work_query, (technician_id,))
            
            return json.dumps({
                "success": True,
                "technician": results[0],
                "recent_work_stats": work_stats[0] if work_stats else None
            }, indent=2)
        else:
            # Get all active technicians
            query = """
            SELECT id, name, employee_id, expertise_areas, certification_level, hire_date
            FROM technicians 
            WHERE active = 1
            ORDER BY certification_level DESC, name
            """
            results = db_manager.execute_query(query)
            
            return json.dumps({
                "success": True,
                "active_technicians": len(results),
                "technicians": results
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Technician lookup failed: {str(e)}"
        }, indent=2)


# Import query_validator at the end to avoid circular imports
from utils.query_validator import query_validator