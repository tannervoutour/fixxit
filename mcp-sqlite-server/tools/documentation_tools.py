"""
Documentation-focused MCP tools for machine manual search and retrieval.
Replaces maintenance-focused tools with documentation-focused ones.
"""

import sqlite3
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import json
import re
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection import db_manager

def search_machine_documentation(
    mcp: FastMCP,
    machine_name: Optional[str] = None,
    line_number: Optional[str] = None,
    machine_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for machines and their available documentation.
    
    Args:
        machine_name: Specific machine name (e.g., 'CSP', 'Feeder')
        line_number: Line designation (e.g., 'Line_1', 'Line_2')
        machine_type: Type of machine (e.g., 'separator', 'feeder', 'folder')
    
    Returns:
        Dict containing machine information and available documentation
    """
    try:
        # Build dynamic query
        query = """
            SELECT m.machine_name, m.machine_type, m.line_number, m.sub_machine,
                   m.description, COUNT(d.id) as document_count,
                   COUNT(ds.id) as section_count,
                   GROUP_CONCAT(DISTINCT d.filename) as available_manuals,
                   GROUP_CONCAT(DISTINCT ds.section_name) as available_sections
            FROM machines m
            LEFT JOIN documents d ON m.id = d.machine_id
            LEFT JOIN document_sections ds ON m.id = ds.machine_id
            WHERE 1=1
        """
        params = []
        
        if machine_name:
            query += " AND m.machine_name LIKE ?"
            params.append(f"%{machine_name}%")
        
        if line_number:
            query += " AND m.line_number = ?"
            params.append(line_number)
            
        if machine_type:
            query += " AND m.machine_type = ?"
            params.append(machine_type)
        
        query += " GROUP BY m.id ORDER BY m.machine_name"
        
        results = db_manager.execute_query(query, tuple(params))
        
        machines = []
        for row in results:
            machine = {
                'machine_name': row['machine_name'],
                'machine_type': row['machine_type'],
                'line_number': row['line_number'],
                'sub_machine': row['sub_machine'],
                'description': row['description'],
                'document_count': row['document_count'],
                'section_count': row['section_count'],
                'available_manuals': row['available_manuals'].split(',') if row['available_manuals'] else [],
                'available_sections': row['available_sections'].split(',') if row['available_sections'] else []
            }
            machines.append(machine)
        
        return {
            'success': True,
            'machines_found': len(machines),
            'machines': machines
        }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'machines': []
        }


def get_manual_sections(
    mcp: FastMCP,
    machine_name: Optional[str] = None,
    section_name: Optional[str] = None,
    document_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get available sections from machine manuals.
    
    Args:
        machine_name: Machine to search for
        section_name: Specific section name to filter by
        document_filename: Specific document filename to filter by
    
    Returns:
        Dict containing section information
    """
    try:
        query = """
            SELECT m.machine_name, m.line_number, d.filename,
                   ds.section_name, ds.section_title, ds.start_page,
                   ds.word_count, ds.keywords
            FROM document_sections ds
            JOIN machines m ON ds.machine_id = m.id
            JOIN documents d ON ds.document_id = d.id
            WHERE d.is_processed = 1
        """
        params = []
        
        if machine_name:
            query += " AND m.machine_name LIKE ?"
            params.append(f"%{machine_name}%")
        
        if section_name:
            query += " AND ds.section_name LIKE ?"
            params.append(f"%{section_name}%")
            
        if document_filename:
            query += " AND d.filename LIKE ?"
            params.append(f"%{document_filename}%")
        
        query += " ORDER BY m.machine_name, d.filename, ds.section_order"
        
        results = db_manager.execute_query(query, tuple(params))
        
        sections = []
        for row in results:
            section = {
                'machine_name': row['machine_name'],
                'line_number': row['line_number'],
                'document': row['filename'],
                'section_name': row['section_name'],
                'section_title': row['section_title'],
                'start_page': row['start_page'],
                'word_count': row['word_count'],
                'keywords': row['keywords'].split(',') if row['keywords'] else []
            }
            sections.append(section)
        
        return {
            'success': True,
            'sections_found': len(sections),
            'sections': sections
        }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'sections': []
        }


def find_troubleshooting_info(
    mcp: FastMCP,
    search_query: str,
    machine_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for troubleshooting information in documentation sections.
    
    Args:
        search_query: Search terms (error symptoms, part names, etc.)
        machine_name: Limit search to specific machine
    
    Returns:
        Dict containing matching troubleshooting sections
    """
    try:
        # Use FTS5 for content search
        query = """
            SELECT m.machine_name, m.line_number, d.filename,
                   ds.section_name, ds.section_title, ds.start_page,
                   snippet(sections_fts, 2, '<b>', '</b>', '...', 30) as content_snippet
            FROM sections_fts 
            JOIN document_sections ds ON sections_fts.rowid = ds.id
            JOIN machines m ON ds.machine_id = m.id
            JOIN documents d ON ds.document_id = d.id
            WHERE sections_fts MATCH ?
        """
        params = [search_query]
        
        if machine_name:
            query += " AND m.machine_name LIKE ?"
            params.append(f"%{machine_name}%")
        
        # Prioritize troubleshooting sections
        query += """
            ORDER BY 
                CASE WHEN ds.section_name LIKE '%troubleshoot%' THEN 1
                     WHEN ds.section_name LIKE '%fault%' THEN 2  
                     WHEN ds.section_name LIKE '%error%' THEN 3
                     WHEN ds.section_name LIKE '%maintenance%' THEN 4
                     ELSE 5 END,
                rank
            LIMIT 20
        """
        
        results = db_manager.execute_query(query, tuple(params))
        
        matches = []
        for row in results:
            match = {
                'machine_name': row['machine_name'],
                'line_number': row['line_number'],
                'document': row['filename'],
                'section_name': row['section_name'],
                'section_title': row['section_title'],
                'start_page': row['start_page'],
                'content_snippet': row['content_snippet']
            }
            matches.append(match)
        
        return {
            'success': True,
            'matches_found': len(matches),
            'search_query': search_query,
            'matches': matches
        }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'matches': []
        }


def get_section_content(
    mcp: FastMCP,
    machine_name: str,
    section_name: str,
    document_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the full content of a specific section.
    
    Args:
        machine_name: Name of the machine
        section_name: Name of the section to retrieve
        document_filename: Specific document (optional if machine has multiple)
    
    Returns:
        Dict containing full section content
    """
    try:
        query = """
            SELECT m.machine_name, d.filename, ds.section_name, 
                   ds.section_title, ds.start_page, ds.end_page,
                   ds.content_text, ds.keywords, ds.word_count
            FROM document_sections ds
            JOIN machines m ON ds.machine_id = m.id
            JOIN documents d ON ds.document_id = d.id
            WHERE m.machine_name = ? AND ds.section_name LIKE ?
        """
        params = [machine_name, f"%{section_name}%"]
        
        if document_filename:
            query += " AND d.filename = ?"
            params.append(document_filename)
        
        query += " ORDER BY ds.section_order LIMIT 1"
        
        results = db_manager.execute_query(query, tuple(params))
        
        if results:
            result = results[0]
            return {
                'success': True,
                'machine_name': result['machine_name'],
                'document': result['filename'],
                'section_name': result['section_name'],
                'section_title': result['section_title'],
                'start_page': result['start_page'],
                'end_page': result['end_page'],
                'content': result['content_text'],
                'keywords': result['keywords'].split(',') if result['keywords'] else [],
                'word_count': result['word_count']
            }
        else:
            return {
                'success': False,
                'error': f"Section '{section_name}' not found for machine '{machine_name}'",
                'content': None
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'content': None
        }


def search_procedures(
    mcp: FastMCP,
    procedure_type: str,
    machine_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for specific types of procedures across documentation.
    
    Args:
        procedure_type: Type of procedure (safety, operation, maintenance, etc.)
        machine_name: Limit search to specific machine
    
    Returns:
        Dict containing matching procedure sections
    """
    try:
        # Search for sections matching procedure type
        query = """
            SELECT m.machine_name, m.line_number, d.filename,
                   ds.section_name, ds.section_title, ds.start_page,
                   ds.word_count, ds.keywords
            FROM document_sections ds
            JOIN machines m ON ds.machine_id = m.id
            JOIN documents d ON ds.document_id = d.id
            WHERE (ds.section_name LIKE ? OR ds.section_title LIKE ? OR ds.keywords LIKE ?)
        """
        search_term = f"%{procedure_type}%"
        params = [search_term, search_term, search_term]
        
        if machine_name:
            query += " AND m.machine_name LIKE ?"
            params.append(f"%{machine_name}%")
        
        query += " ORDER BY m.machine_name, ds.section_order"
        
        results = db_manager.execute_query(query, tuple(params))
        
        procedures = []
        for row in results:
            procedure = {
                'machine_name': row['machine_name'],
                'line_number': row['line_number'],
                'document': row['filename'],
                'section_name': row['section_name'],
                'section_title': row['section_title'],
                'start_page': row['start_page'],
                'word_count': row['word_count'],
                'keywords': row['keywords'].split(',') if row['keywords'] else []
            }
            procedures.append(procedure)
        
        return {
            'success': True,
            'procedure_type': procedure_type,
            'procedures_found': len(procedures),
            'procedures': procedures
        }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'procedures': []
        }


def get_documentation_overview(
    mcp: FastMCP
) -> Dict[str, Any]:
    """
    Get an overview of the documentation database status and contents.
    
    Returns:
        Dict containing database statistics and overview
    """
    try:
        # Get overall statistics
        stats = {}
        
        # Machine count
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM machines")
        stats['total_machines'] = result[0]['count']
        
        # Document count
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM documents")
        stats['total_documents'] = result[0]['count']
        
        # Processed documents
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM documents WHERE is_processed = 1")
        stats['processed_documents'] = result[0]['count']
        
        # Total sections
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM document_sections")
        stats['total_sections'] = result[0]['count']
        
        # Total pages
        result = db_manager.execute_query("SELECT SUM(page_count) as total FROM documents")
        stats['total_pages'] = result[0]['total'] if result[0]['total'] else 0
        
        # Machine breakdown
        machine_breakdown_results = db_manager.execute_query("""
            SELECT m.machine_name, m.machine_type, m.line_number,
                   COUNT(DISTINCT d.id) as documents,
                   COUNT(ds.id) as sections
            FROM machines m
            LEFT JOIN documents d ON m.id = d.machine_id
            LEFT JOIN document_sections ds ON m.id = ds.machine_id
            GROUP BY m.id
            ORDER BY m.machine_name
        """)
        
        machine_breakdown = []
        for row in machine_breakdown_results:
            machine_breakdown.append({
                'machine_name': row['machine_name'],
                'machine_type': row['machine_type'],
                'line_number': row['line_number'],
                'documents': row['documents'],
                'sections': row['sections']
            })
        
        return {
            'success': True,
            'database_stats': stats,
            'machine_breakdown': machine_breakdown,
            'processing_status': f"{stats['processed_documents']}/{stats['total_documents']} documents processed"
        }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'database_stats': {}
        }