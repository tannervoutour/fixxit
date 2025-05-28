#!/usr/bin/env python3
"""Test the fixed documentation tools with the Tunnels machine."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-sqlite-server'))

from tools.documentation_tools import search_machine_documentation

def test_tunnels_search():
    """Test searching for Tunnels machine with fixed tools."""
    
    print("🧪 Testing fixed documentation tools...")
    print("=" * 60)
    
    # Test the search function directly
    print("📝 Testing search_machine_documentation for 'Tunnels'...")
    
    # Note: We pass None for mcp parameter since we're using db_manager now
    result = search_machine_documentation(
        mcp=None,  # Not used anymore
        machine_name="Tunnels",
        line_number=None,
        machine_type=None
    )
    
    print("🎯 Result:")
    print(f"Success: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"Machines found: {result.get('machines_found', 0)}")
        
        for machine in result.get('machines', []):
            print(f"\n📋 Machine: {machine['machine_name']}")
            print(f"   Type: {machine['machine_type']}")
            print(f"   Line: {machine['line_number']}")
            print(f"   Documents: {machine['document_count']}")
            print(f"   Sections: {machine['section_count']}")
            
            if machine['available_manuals']:
                print(f"   Manuals: {machine['available_manuals'][:3]}...")  # Show first 3
            
            if machine['available_sections']:
                print(f"   Sections: {machine['available_sections'][:5]}...")  # Show first 5
                
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    # Test exact match
    print(f"\n📝 Testing exact match for 'Tunnels'...")
    result2 = search_machine_documentation(
        mcp=None,
        machine_name="Tunnels",  # Exact match
        line_number=None,
        machine_type=None
    )
    
    print(f"Exact match success: {result2.get('success', False)}")
    print(f"Exact match found: {result2.get('machines_found', 0)} machines")
    
    return result.get('success', False)

if __name__ == "__main__":
    success = test_tunnels_search()
    if success:
        print(f"\n✅ SUCCESS: Fixed tools can access Tunnels machine data!")
    else:
        print(f"\n❌ FAILURE: Tools still not working properly")