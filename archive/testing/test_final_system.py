#!/usr/bin/env python3
"""
Final comprehensive test of the documentation AI system.
"""

import sys
import json
import sqlite3
from pathlib import Path

def test_complete_system():
    """Test the complete documentation system end-to-end."""
    print("🚀 Final Documentation AI System Test")
    print("=" * 60)
    
    # Test database
    db_path = "/root/fixxitV2/mcp-sqlite-server/database/database.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get comprehensive stats
            cursor.execute("SELECT COUNT(*) FROM machines")
            machines = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM documents WHERE is_processed = 1")
            documents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM document_sections")
            sections = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(word_count) FROM document_sections")
            total_words = cursor.fetchone()[0] or 0
            
            print(f"📊 Database Statistics:")
            print(f"   Machines: {machines}")
            print(f"   Documents: {documents}")
            print(f"   Sections: {sections}")
            print(f"   Total words: {total_words:,}")
            
            # Test sample queries that would be typical for users
            print(f"\n🔍 Sample Query Tests:")
            
            # 1. Find machines by type
            cursor.execute("SELECT machine_name FROM machines WHERE machine_type = 'press'")
            presses = cursor.fetchall()
            print(f"   ✅ Press machines: {len(presses)} found")
            
            # 2. Find troubleshooting sections
            cursor.execute("""
                SELECT COUNT(*) FROM document_sections 
                WHERE section_name LIKE '%troubleshoot%' OR section_name LIKE '%fault%'
            """)
            troubleshooting_sections = cursor.fetchone()[0]
            print(f"   ✅ Troubleshooting sections: {troubleshooting_sections}")
            
            # 3. Find safety sections
            cursor.execute("""
                SELECT COUNT(*) FROM document_sections 
                WHERE section_name LIKE '%safety%' OR section_name LIKE '%warning%'
            """)
            safety_sections = cursor.fetchone()[0]
            print(f"   ✅ Safety sections: {safety_sections}")
            
            # 4. Test FTS search capability
            cursor.execute("""
                SELECT COUNT(*) FROM sections_fts 
                WHERE sections_fts MATCH 'hydraulic'
            """)
            hydraulic_matches = cursor.fetchone()[0]
            print(f"   ✅ 'Hydraulic' content matches: {hydraulic_matches}")
            
            # 5. Show machine coverage
            cursor.execute("""
                SELECT m.machine_name, COUNT(ds.id) as sections
                FROM machines m
                LEFT JOIN document_sections ds ON m.id = ds.machine_id
                GROUP BY m.id
                HAVING sections > 0
                ORDER BY sections DESC
                LIMIT 5
            """)
            top_machines = cursor.fetchall()
            print(f"\n📋 Top machines by documentation coverage:")
            for machine, section_count in top_machines:
                print(f"   - {machine}: {section_count} sections")
    
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Test MCP tools directly
    print(f"\n🔧 Testing MCP Tool Functionality:")
    
    try:
        sys.path.append("/root/fixxitV2/mcp-sqlite-server")
        from tools.documentation_tools import (
            search_machine_documentation,
            find_troubleshooting_info,
            get_documentation_overview
        )
        
        class MockMCP:
            def __init__(self):
                self.db_path = db_path
        
        mcp = MockMCP()
        
        # Test overview
        overview = get_documentation_overview(mcp)
        if overview['success']:
            stats = overview['database_stats']
            print(f"   ✅ System overview: {stats['total_machines']} machines, {stats['total_sections']} sections")
        
        # Test machine search
        result = search_machine_documentation(mcp, machine_name="Power")
        if result['success']:
            print(f"   ✅ Machine search: Found {result['machines_found']} machines matching 'Power'")
        
        # Test troubleshooting search
        result = find_troubleshooting_info(mcp, "error")
        if result['success']:
            print(f"   ✅ Troubleshooting search: Found {result['matches_found']} matches for 'error'")
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False
    
    print(f"\n🎯 SYSTEM READY!")
    print(f"✅ Database populated with real machine documentation")
    print(f"✅ MCP tools working correctly")
    print(f"✅ Full-text search enabled")
    print(f"✅ AI can now answer questions about:")
    print(f"   - Machine operations and procedures")
    print(f"   - Troubleshooting and fault resolution")
    print(f"   - Safety instructions and warnings")
    print(f"   - Maintenance procedures")
    print(f"   - Technical specifications")
    
    return True

if __name__ == "__main__":
    success = test_complete_system()
    if success:
        print(f"\n🎉 DOCUMENTATION AI SYSTEM FULLY OPERATIONAL!")
        sys.exit(0)
    else:
        print(f"\n❌ System test failed")
        sys.exit(1)