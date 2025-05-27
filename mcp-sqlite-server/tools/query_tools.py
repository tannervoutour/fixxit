"""MCP tools for executing database queries safely."""

import json
from typing import Any, Dict, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection import db_manager
from utils.query_validator import query_validator


def execute_query(query: str, limit: Optional[int] = 100) -> str:
    """
    Execute a SELECT query against the maintenance database.
    
    Args:
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return (default 100, max 1000)
        
    Returns:
        JSON string with query results or error message
    """
    try:
        # Validate the query
        is_valid, error_msg = query_validator.validate_query(query)
        if not is_valid:
            return json.dumps({
                "error": f"Invalid query: {error_msg}",
                "query": query
            }, indent=2)
        
        # Apply limit if not already specified
        if limit is not None:
            limit = min(max(1, limit), 1000)  # Clamp between 1 and 1000
            if "limit" not in query.lower():
                query = f"{query.rstrip(';')} LIMIT {limit}"
        
        # Execute query
        results = db_manager.execute_query(query)
        
        return json.dumps({
            "success": True,
            "row_count": len(results),
            "query": query,
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Query execution failed: {str(e)}",
            "query": query
        }, indent=2)


def search_machines(
    location: Optional[str] = None,
    status: Optional[str] = None,
    model: Optional[str] = None,
    manufacturer: Optional[str] = None
) -> str:
    """
    Search for machines based on various criteria.
    
    Args:
        location: Filter by machine location (partial match)
        status: Filter by machine status (operational, maintenance, down, retired)
        model: Filter by machine model (partial match)
        manufacturer: Filter by manufacturer (partial match)
        
    Returns:
        JSON string with search results
    """
    try:
        # Build WHERE clause dynamically
        where_conditions = []
        params = []
        
        if location:
            where_conditions.append("location LIKE ?")
            params.append(f"%{location}%")
        
        if status:
            where_conditions.append("status = ?")
            params.append(status)
        
        if model:
            where_conditions.append("model LIKE ?")
            params.append(f"%{model}%")
        
        if manufacturer:
            where_conditions.append("manufacturer LIKE ?")
            params.append(f"%{manufacturer}%")
        
        # Base query
        query = """
        SELECT id, serial_number, model, manufacturer, location, status, 
               install_date, last_maintenance, next_maintenance
        FROM machines
        """
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " ORDER BY location, serial_number"
        
        # Execute with parameters (safe from injection)
        results = db_manager.execute_query(query, tuple(params) if params else None)
        
        return json.dumps({
            "success": True,
            "search_criteria": {
                "location": location,
                "status": status,
                "model": model,
                "manufacturer": manufacturer
            },
            "machine_count": len(results),
            "machines": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Machine search failed: {str(e)}"
        }, indent=2)


def get_trouble_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    machine_id: Optional[int] = None,
    limit: Optional[int] = 50
) -> str:
    """
    Get trouble tickets with optional filtering.
    
    Args:
        status: Filter by ticket status (open, assigned, in_progress, resolved, closed)
        priority: Filter by priority (low, medium, high, urgent)
        machine_id: Filter by specific machine ID
        limit: Maximum number of tickets to return
        
    Returns:
        JSON string with ticket results
    """
    try:
        where_conditions = []
        params = []
        
        if status:
            where_conditions.append("tt.status = ?")
            params.append(status)
        
        if priority:
            where_conditions.append("tt.priority = ?")
            params.append(priority)
        
        if machine_id:
            where_conditions.append("tt.machine_id = ?")
            params.append(machine_id)
        
        query = """
        SELECT tt.id, tt.machine_id, m.serial_number, m.model, m.location,
               tt.reported_by, tt.date_reported, tt.status, tt.priority,
               tt.fault_code, tt.description, tt.resolution,
               t.name as assigned_technician, tt.resolved_date
        FROM trouble_tickets tt
        JOIN machines m ON tt.machine_id = m.id
        LEFT JOIN technicians t ON tt.assigned_technician_id = t.id
        """
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " ORDER BY tt.priority DESC, tt.date_reported DESC"
        
        if limit:
            query += f" LIMIT {min(max(1, limit), 200)}"
        
        results = db_manager.execute_query(query, tuple(params) if params else None)
        
        return json.dumps({
            "success": True,
            "filter_criteria": {
                "status": status,
                "priority": priority,
                "machine_id": machine_id
            },
            "ticket_count": len(results),
            "tickets": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Trouble ticket query failed: {str(e)}"
        }, indent=2)


def get_maintenance_history(
    machine_id: Optional[int] = None,
    technician_id: Optional[int] = None,
    maintenance_type: Optional[str] = None,
    days_back: Optional[int] = 30
) -> str:
    """
    Get maintenance history records with filtering.
    
    Args:
        machine_id: Filter by specific machine ID
        technician_id: Filter by specific technician ID
        maintenance_type: Filter by type (preventive, corrective, emergency, inspection)
        days_back: How many days back to look (default 30)
        
    Returns:
        JSON string with maintenance history
    """
    try:
        where_conditions = ["mr.maintenance_date >= date('now', '-' || ? || ' days')"]
        params = [days_back or 30]
        
        if machine_id:
            where_conditions.append("mr.machine_id = ?")
            params.append(machine_id)
        
        if technician_id:
            where_conditions.append("mr.technician_id = ?")
            params.append(technician_id)
        
        if maintenance_type:
            where_conditions.append("mr.maintenance_type = ?")
            params.append(maintenance_type)
        
        query = """
        SELECT mr.id, mr.machine_id, m.serial_number, m.model, m.location,
               mr.technician_id, t.name as technician_name,
               mr.maintenance_date, mr.maintenance_type, mr.description,
               mr.parts_used, mr.labor_hours, mr.status, mr.notes
        FROM maintenance_records mr
        JOIN machines m ON mr.machine_id = m.id
        JOIN technicians t ON mr.technician_id = t.id
        WHERE """ + " AND ".join(where_conditions) + """
        ORDER BY mr.maintenance_date DESC
        """
        
        results = db_manager.execute_query(query, tuple(params))
        
        return json.dumps({
            "success": True,
            "filter_criteria": {
                "machine_id": machine_id,
                "technician_id": technician_id,
                "maintenance_type": maintenance_type,
                "days_back": days_back
            },
            "record_count": len(results),
            "maintenance_records": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Maintenance history query failed: {str(e)}"
        }, indent=2)


def search_parts(
    part_number: Optional[str] = None,
    name: Optional[str] = None,
    compatible_model: Optional[str] = None,
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
    try:
        where_conditions = []
        params = []
        
        if part_number:
            where_conditions.append("part_number LIKE ?")
            params.append(f"%{part_number}%")
        
        if name:
            where_conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        
        if compatible_model:
            where_conditions.append("compatible_models LIKE ?")
            params.append(f"%{compatible_model}%")
        
        if low_stock_only:
            where_conditions.append("stock_quantity <= min_stock_level")
        
        query = """
        SELECT part_number, name, description, compatible_models,
               stock_quantity, min_stock_level, storage_location,
               unit_cost, supplier, last_ordered,
               CASE WHEN stock_quantity <= min_stock_level THEN 'LOW' ELSE 'OK' END as stock_status
        FROM parts_inventory
        """
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " ORDER BY stock_status DESC, part_number"
        
        results = db_manager.execute_query(query, tuple(params) if params else None)
        
        return json.dumps({
            "success": True,
            "search_criteria": {
                "part_number": part_number,
                "name": name,
                "compatible_model": compatible_model,
                "low_stock_only": low_stock_only
            },
            "parts_count": len(results),
            "parts": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Parts search failed: {str(e)}"
        }, indent=2)