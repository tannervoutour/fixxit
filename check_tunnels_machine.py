#!/usr/bin/env python3
"""Check if Tunnels machine exists in the database."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-sqlite-server'))

from utils.db_connection import db_manager

def check_machines():
    """Check what machines are available, especially looking for Tunnels."""
    
    print("🔍 Checking available machines in database...")
    
    try:
        # Get all machines
        query = "SELECT machine_name, machine_type, line_number, sub_machine FROM machines ORDER BY machine_name"
        machines = db_manager.execute_query(query)
        
        print(f"\n📋 Found {len(machines)} machines:")
        for machine in machines:
            print(f"  - {machine['machine_name']} ({machine['machine_type']}) - Line: {machine['line_number']}")
        
        # Check for Tunnels specifically
        tunnel_machines = [m for m in machines if 'tunnel' in m['machine_name'].lower()]
        print(f"\n🎯 Machines with 'tunnel' in name: {len(tunnel_machines)}")
        for machine in tunnel_machines:
            print(f"  - {machine['machine_name']} ({machine['machine_type']})")
        
        # Check for case variations
        print(f"\n🔍 Checking case variations for 'Tunnels':")
        variations = ['Tunnels', 'tunnels', 'Tunnel', 'tunnel', 'TUNNELS']
        for variation in variations:
            matches = [m for m in machines if variation in m['machine_name']]
            if matches:
                print(f"  ✅ Found matches for '{variation}': {[m['machine_name'] for m in matches]}")
            else:
                print(f"  ❌ No matches for '{variation}'")
        
        # Check documents for any machine
        print(f"\n📚 Checking documents table...")
        doc_query = "SELECT COUNT(*) as count FROM documents"
        doc_count = db_manager.execute_query(doc_query)
        print(f"  Total documents: {doc_count[0]['count']}")
        
        # Check sections
        section_query = "SELECT COUNT(*) as count FROM document_sections"
        section_count = db_manager.execute_query(section_query)
        print(f"  Total sections: {section_count[0]['count']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_machines()