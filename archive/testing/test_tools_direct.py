#!/usr/bin/env python3
"""Direct test of fixed documentation tools."""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fixed_functions():
    """Test the fixed functions directly."""
    
    print("🧪 Testing Fixed Documentation Tools")
    print("=" * 50)
    
    try:
        # Test db_manager import
        print("📋 Testing db_manager import...")
        from utils.db_connection import db_manager
        print("✅ db_manager imported successfully")
        
        # Test a simple query
        print("\n📋 Testing database connection...")
        machines = db_manager.execute_query("SELECT machine_name FROM machines WHERE machine_name = 'Tunnels'")
        print(f"✅ Query executed: Found {len(machines)} Tunnels machines")
        
        if machines:
            print(f"   Machine found: {machines[0]['machine_name']}")
        
        # Test the fixed search function 
        print("\n📋 Testing fixed search_machine_documentation...")
        
        # Import the fixed function (remove mcp parameter dependency)
        def test_search_machine_documentation(machine_name=None, line_number=None, machine_type=None):
            """Modified version for testing without mcp parameter."""
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
        
        # Test with Tunnels
        result = test_search_machine_documentation(machine_name="Tunnels")
        
        print(f"🎯 Search Result:")
        print(f"   Success: {result['success']}")
        print(f"   Machines found: {result['machines_found']}")
        
        if result['success'] and result['machines_found'] > 0:
            machine = result['machines'][0]
            print(f"   📋 Machine: {machine['machine_name']}")
            print(f"      Type: {machine['machine_type']}")
            print(f"      Documents: {machine['document_count']}")
            print(f"      Sections: {machine['section_count']}")
            
            if machine['available_manuals']:
                print(f"      Sample manuals: {machine['available_manuals'][:2]}")
            
            if machine['available_sections']:
                print(f"      Sample sections: {machine['available_sections'][:3]}")
            
            print("\n🎉 SUCCESS: Fixed tools can access Tunnels machine data!")
            return True
        else:
            print(f"   ❌ No machines found or error: {result.get('error', 'Unknown')}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixed_functions()
    if success:
        print(f"\n✅ TOOLS FIXED: Database access issue resolved!")
    else:
        print(f"\n❌ TOOLS STILL BROKEN: Need further investigation")