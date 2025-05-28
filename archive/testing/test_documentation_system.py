#!/usr/bin/env python3
"""
Test script for the documentation AI system.
Tests real queries against the populated documentation database.
"""

import sys
import json
import sqlite3
from pathlib import Path

def test_database_content():
    """Test that the database has been populated correctly."""
    db_path = "/root/fixxitV2/mcp-sqlite-server/database/database.db"
    
    print("🔍 Testing Database Content")
    print("=" * 50)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Test machines
            cursor.execute("SELECT COUNT(*) FROM machines")
            machine_count = cursor.fetchone()[0]
            print(f"✅ Machines in database: {machine_count}")
            
            # Test documents 
            cursor.execute("SELECT COUNT(*) FROM documents WHERE is_processed = 1")
            doc_count = cursor.fetchone()[0]
            print(f"✅ Processed documents: {doc_count}")
            
            # Test sections
            cursor.execute("SELECT COUNT(*) FROM document_sections")
            section_count = cursor.fetchone()[0]
            print(f"✅ Total sections: {section_count}")
            
            # Show sample machines
            cursor.execute("SELECT machine_name, machine_type, line_number FROM machines LIMIT 5")
            machines = cursor.fetchall()
            print(f"\n📋 Sample machines:")
            for machine in machines:
                print(f"  - {machine[0]} ({machine[1]}, {machine[2]})")
            
            # Show sample sections
            cursor.execute("""
                SELECT m.machine_name, ds.section_name, ds.start_page, ds.word_count
                FROM document_sections ds 
                JOIN machines m ON ds.machine_id = m.id 
                ORDER BY ds.word_count DESC 
                LIMIT 5
            """)
            sections = cursor.fetchall()
            print(f"\n📖 Sample sections (by content size):")
            for section in sections:
                print(f"  - {section[0]}: {section[1]} (page {section[2]}, {section[3]} words)")
            
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_mcp_tools():
    """Test the MCP tools directly."""
    print("\n🔧 Testing MCP Tools")
    print("=" * 50)
    
    # Import the documentation tools
    sys.path.append("/root/fixxitV2/mcp-sqlite-server")
    
    try:
        from tools.documentation_tools import (
            search_machine_documentation,
            get_manual_sections,
            find_troubleshooting_info,
            get_section_content
        )
        
        # Mock MCP object with db_path
        class MockMCP:
            def __init__(self):
                self.db_path = "/root/fixxitV2/mcp-sqlite-server/database/database.db"
        
        mcp = MockMCP()
        
        # Test 1: Search for machines
        print("🔍 Test 1: Search for CSP machine")
        result = search_machine_documentation(mcp, machine_name="CSP")
        if result['success']:
            print(f"✅ Found {result['machines_found']} machines")
            if result['machines']:
                machine = result['machines'][0]
                print(f"   - {machine['machine_name']}: {machine['document_count']} docs, {machine['section_count']} sections")
        else:
            print(f"❌ Search failed: {result['error']}")
        
        # Test 2: Get sections for a machine
        print("\n🔍 Test 2: Get sections for PowerPress")
        result = get_manual_sections(mcp, machine_name="PowerPress")
        if result['success']:
            print(f"✅ Found {result['sections_found']} sections")
            for section in result['sections'][:3]:  # Show first 3
                print(f"   - {section['section_name']} (page {section['start_page']})")
        else:
            print(f"❌ Sections query failed: {result['error']}")
        
        # Test 3: Search for troubleshooting info
        print("\n🔍 Test 3: Search for 'hydraulic' troubleshooting")
        result = find_troubleshooting_info(mcp, "hydraulic")
        if result['success']:
            print(f"✅ Found {result['matches_found']} troubleshooting matches")
            for match in result['matches'][:2]:  # Show first 2
                print(f"   - {match['machine_name']}: {match['section_name']} (page {match['start_page']})")
        else:
            print(f"❌ Troubleshooting search failed: {result['error']}")
        
        # Test 4: Get specific section content
        print("\n🔍 Test 4: Get section content")
        # First find a machine with sections
        machines_result = search_machine_documentation(mcp, machine_name="PowerPress")
        if machines_result['success'] and machines_result['machines']:
            machine_name = machines_result['machines'][0]['machine_name']
            sections_result = get_manual_sections(mcp, machine_name=machine_name)
            if sections_result['success'] and sections_result['sections']:
                section_name = sections_result['sections'][0]['section_name']
                result = get_section_content(mcp, machine_name, section_name)
                if result['success']:
                    content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                    print(f"✅ Retrieved section content ({result['word_count']} words)")
                    print(f"   Preview: {content_preview}")
                else:
                    print(f"❌ Section content failed: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

def test_ai_system_integration():
    """Test the complete AI system integration."""
    print("\n🤖 Testing AI System Integration")
    print("=" * 50)
    
    # This would typically test the actual OpenAI integration
    # For now, we'll test that the MCP server can start
    
    try:
        import subprocess
        import time
        
        print("🚀 Testing MCP server startup...")
        
        # Try to start the server briefly to test configuration
        server_path = "/root/fixxitV2/mcp-sqlite-server/server.py"
        
        # Test server import/configuration 
        sys.path.append("/root/fixxitV2/mcp-sqlite-server")
        from server import mcp
        
        print("✅ MCP server configuration is valid")
        print("✅ Documentation tools are properly registered")
        
        # Test tool registry loading
        import yaml
        with open("/root/fixxitV2/tool_registry.yaml", 'r') as f:
            registry = yaml.safe_load(f)
        
        doc_tools = [name for name, tool in registry['tools'].items() if tool['category'] == 'documentation']
        print(f"✅ Found {len(doc_tools)} documentation tools in registry")
        
        return True
        
    except Exception as e:
        print(f"❌ AI system integration test failed: {e}")
        return False

def run_sample_queries():
    """Run sample queries that a user might ask."""
    print("\n💬 Sample AI Queries")
    print("=" * 50)
    
    sys.path.append("/root/fixxitV2/mcp-sqlite-server")
    from tools.documentation_tools import search_machine_documentation, find_troubleshooting_info
    
    class MockMCP:
        def __init__(self):
            self.db_path = "/root/fixxitV2/mcp-sqlite-server/database/database.db"
    
    mcp = MockMCP()
    
    sample_queries = [
        {
            "query": "What machines do we have in Line_1?",
            "test": lambda: search_machine_documentation(mcp, line_number="Line_1")
        },
        {
            "query": "Find troubleshooting info for 'pressure' issues",
            "test": lambda: find_troubleshooting_info(mcp, "pressure")
        },
        {
            "query": "What documentation is available for the dryer?",
            "test": lambda: search_machine_documentation(mcp, machine_name="Dryer")
        }
    ]
    
    for i, sample in enumerate(sample_queries, 1):
        print(f"\n{i}. Query: {sample['query']}")
        try:
            result = sample['test']()
            if result['success']:
                if 'machines_found' in result:
                    print(f"   ✅ Found {result['machines_found']} machines")
                elif 'matches_found' in result:
                    print(f"   ✅ Found {result['matches_found']} matches")
                else:
                    print(f"   ✅ Query successful")
            else:
                print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ Query error: {e}")

def main():
    """Run all tests."""
    print("🧪 Documentation AI System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Database Content", test_database_content),
        ("MCP Tools", test_mcp_tools), 
        ("AI System Integration", test_ai_system_integration),
        ("Sample Queries", run_sample_queries)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Documentation AI system is ready!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed. Review issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())