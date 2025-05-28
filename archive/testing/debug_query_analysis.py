#!/usr/bin/env python3
"""
Debug script to analyze AI query processing and identify issues.
"""

import os
import sys
import sqlite3
import json
from pathlib import Path

# Set API key
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

def analyze_database_content():
    """Analyze what's actually in the database for troubleshooting."""
    print("🔍 DATABASE CONTENT ANALYSIS")
    print("=" * 60)
    
    db_path = "/root/fixxitV2/mcp-sqlite-server/database/database.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check machines
            print("📱 MACHINES:")
            cursor.execute("SELECT machine_name, machine_type, line_number FROM machines ORDER BY machine_name")
            machines = cursor.fetchall()
            for machine in machines[:10]:  # Show first 10
                print(f"   - {machine[0]} ({machine[1]}, {machine[2]})")
            if len(machines) > 10:
                print(f"   ... and {len(machines) - 10} more machines")
            
            # Check sample sections for PowerPress
            print(f"\n📖 POWERPRESS SECTIONS:")
            cursor.execute("""
                SELECT ds.section_name, ds.start_page, ds.word_count, d.filename
                FROM document_sections ds
                JOIN documents d ON ds.document_id = d.id
                JOIN machines m ON ds.machine_id = m.id
                WHERE m.machine_name = 'PowerPress'
                ORDER BY ds.section_order
                LIMIT 10
            """)
            sections = cursor.fetchall()
            for section in sections:
                print(f"   - {section[0]} (page {section[1]}, {section[2]} words) - {section[3]}")
            
            # Check for safety-related sections
            print(f"\n🛡️ SAFETY SECTIONS (any machine):")
            cursor.execute("""
                SELECT m.machine_name, ds.section_name, ds.start_page, ds.word_count
                FROM document_sections ds
                JOIN machines m ON ds.machine_id = m.id
                WHERE ds.section_name LIKE '%safety%' OR ds.section_name LIKE '%Safety%'
                ORDER BY ds.word_count DESC
                LIMIT 5
            """)
            safety_sections = cursor.fetchall()
            for section in safety_sections:
                print(f"   - {section[0]}: {section[1]} (page {section[2]}, {section[3]} words)")
            
            # Test FTS search
            print(f"\n🔍 FULL-TEXT SEARCH TEST:")
            cursor.execute("""
                SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH 'safety'
            """)
            safety_matches = cursor.fetchone()[0]
            print(f"   'safety' matches: {safety_matches}")
            
            cursor.execute("""
                SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH 'PowerPress'
            """)
            powerpress_matches = cursor.fetchone()[0]
            print(f"   'PowerPress' matches: {powerpress_matches}")
            
            # Sample content from a safety section
            print(f"\n📄 SAMPLE SAFETY CONTENT:")
            cursor.execute("""
                SELECT ds.content_text
                FROM document_sections ds
                JOIN machines m ON ds.machine_id = m.id
                WHERE m.machine_name = 'PowerPress' AND ds.section_name LIKE '%safety%'
                LIMIT 1
            """)
            content = cursor.fetchone()
            if content and content[0]:
                preview = content[0][:300] + "..." if len(content[0]) > 300 else content[0]
                print(f"   Preview: {preview}")
            else:
                print("   No safety content found for PowerPress")
            
    except Exception as e:
        print(f"❌ Database analysis failed: {e}")

def test_mcp_tools_directly():
    """Test the MCP tools directly to see what they return."""
    print(f"\n🔧 DIRECT MCP TOOLS TEST")
    print("=" * 60)
    
    sys.path.append("/root/fixxitV2/mcp-sqlite-server")
    
    try:
        from tools.documentation_tools import (
            search_machine_documentation,
            get_manual_sections,
            search_procedures,
            find_troubleshooting_info
        )
        
        class MockMCP:
            def __init__(self):
                self.db_path = "/root/fixxitV2/mcp-sqlite-server/database/database.db"
        
        mcp = MockMCP()
        
        # Test 1: Search for PowerPress
        print("🔍 Test 1: Search for PowerPress machine")
        result = search_machine_documentation(mcp, machine_name="PowerPress")
        print(f"   Success: {result['success']}")
        if result['success']:
            print(f"   Machines found: {result['machines_found']}")
            if result['machines']:
                machine = result['machines'][0]
                print(f"   - {machine['machine_name']}: {machine['document_count']} docs, {machine['section_count']} sections")
                print(f"   - Available sections: {machine['available_sections'][:200]}...")
        
        # Test 2: Get PowerPress sections
        print(f"\n🔍 Test 2: Get PowerPress sections")
        result = get_manual_sections(mcp, machine_name="PowerPress")
        print(f"   Success: {result['success']}")
        if result['success']:
            print(f"   Sections found: {result['sections_found']}")
            for section in result['sections'][:5]:  # Show first 5
                print(f"   - {section['section_name']} (page {section['start_page']})")
        
        # Test 3: Search for safety procedures
        print(f"\n🔍 Test 3: Search for safety procedures")
        result = search_procedures(mcp, procedure_type="safety", machine_name="PowerPress")
        print(f"   Success: {result['success']}")
        if result['success']:
            print(f"   Procedures found: {result['procedures_found']}")
            for procedure in result['procedures'][:3]:  # Show first 3
                print(f"   - {procedure['section_name']} (page {procedure['start_page']})")
        
        # Test 4: Full-text search for safety
        print(f"\n🔍 Test 4: Full-text search for 'safety PowerPress'")
        result = find_troubleshooting_info(mcp, "safety PowerPress")
        print(f"   Success: {result['success']}")
        if result['success']:
            print(f"   Matches found: {result['matches_found']}")
            for match in result['matches'][:3]:  # Show first 3
                print(f"   - {match['machine_name']}: {match['section_name']} (page {match['start_page']})")
                if 'content_snippet' in match:
                    print(f"     Snippet: {match['content_snippet'][:100]}...")
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        import traceback
        traceback.print_exc()

def analyze_search_capabilities():
    """Analyze what search capabilities are working."""
    print(f"\n🔍 SEARCH CAPABILITY ANALYSIS")
    print("=" * 60)
    
    db_path = "/root/fixxitV2/mcp-sqlite-server/database/database.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Test different search approaches
            queries = [
                ("PowerPress machine search", "SELECT COUNT(*) FROM machines WHERE machine_name LIKE '%PowerPress%'"),
                ("Safety sections search", "SELECT COUNT(*) FROM document_sections WHERE section_name LIKE '%safety%'"),
                ("PowerPress sections", "SELECT COUNT(*) FROM document_sections ds JOIN machines m ON ds.machine_id = m.id WHERE m.machine_name = 'PowerPress'"),
                ("FTS safety search", "SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH 'safety'"),
                ("FTS PowerPress search", "SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH 'PowerPress'"),
            ]
            
            for description, query in queries:
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()[0]
                    print(f"   ✅ {description}: {result} results")
                except Exception as e:
                    print(f"   ❌ {description}: Error - {e}")
            
            # Check if FTS is properly populated
            cursor.execute("SELECT COUNT(*) FROM sections_fts")
            fts_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM document_sections")
            sections_count = cursor.fetchone()[0]
            
            print(f"\n📊 Index Status:")
            print(f"   Document sections: {sections_count}")
            print(f"   FTS index entries: {fts_count}")
            if fts_count != sections_count:
                print(f"   ⚠️ FTS index may not be fully populated!")
            else:
                print(f"   ✅ FTS index properly populated")
                
    except Exception as e:
        print(f"❌ Search analysis failed: {e}")

def provide_recommendations():
    """Provide recommendations based on analysis."""
    print(f"\n💡 ANALYSIS RECOMMENDATIONS")
    print("=" * 60)
    
    print("Based on the analysis, check these potential issues:")
    print()
    print("1. 🔍 **Search Function Issues:**")
    print("   - Are the MCP tools returning the right data?")
    print("   - Is the FTS index working properly?")
    print("   - Are machine names being matched correctly?")
    print()
    print("2. 🤖 **AI Decision Making:**")
    print("   - Is the AI choosing the right tools?")
    print("   - Is it interpreting tool results correctly?")
    print("   - Are the tool descriptions clear enough?")
    print()
    print("3. 📊 **Data Quality:**")
    print("   - Are sections properly categorized?")
    print("   - Is content extraction working correctly?")
    print("   - Are keywords properly generated?")
    print()
    print("4. 🔧 **Tool Configuration:**")
    print("   - Are all tools enabled in tool_config.env?")
    print("   - Are tool descriptions accurate?")
    print("   - Is the AI getting proper function definitions?")

def main():
    """Run complete analysis."""
    print("🧪 AI QUERY ANALYSIS & DEBUGGING")
    print("=" * 80)
    
    analyze_database_content()
    test_mcp_tools_directly()
    analyze_search_capabilities()
    provide_recommendations()
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Review the analysis above")
    print("2. Test a specific query with the AI")
    print("3. Compare expected vs actual results")
    print("4. Identify where the process breaks down")

if __name__ == "__main__":
    main()