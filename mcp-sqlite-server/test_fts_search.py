#!/usr/bin/env python3
"""Test Full-Text Search capabilities."""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fts_search():
    """Test Full-Text Search functionality."""
    
    print("🧪 Testing Full-Text Search Capabilities")
    print("=" * 50)
    
    try:
        from utils.db_connection import db_manager
        print("✅ Database connection ready")
        
        # Check if FTS table exists
        print("\n📋 Checking FTS table...")
        try:
            fts_tables = db_manager.execute_query("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%fts%'
            """)
            
            print(f"FTS tables found: {[table['name'] for table in fts_tables]}")
            
            if fts_tables:
                print("✅ FTS search available")
                
                # Test FTS search
                print(f"\n🔍 Testing FTS search for 'safety'...")
                
                # Test the find_troubleshooting function logic
                query = """
                    SELECT m.machine_name, m.line_number, d.filename,
                           ds.section_name, ds.section_title, ds.start_page,
                           snippet(sections_fts, 2, '<b>', '</b>', '...', 30) as content_snippet
                    FROM sections_fts 
                    JOIN document_sections ds ON sections_fts.rowid = ds.id
                    JOIN machines m ON ds.machine_id = m.id
                    JOIN documents d ON ds.document_id = d.id
                    WHERE sections_fts MATCH ?
                    LIMIT 5
                """
                
                results = db_manager.execute_query(query, ("safety",))
                
                print(f"Found {len(results)} matches for 'safety'")
                
                for i, result in enumerate(results[:3], 1):
                    print(f"\n📄 Match {i}:")
                    print(f"   Machine: {result['machine_name']}")
                    print(f"   Section: {result['section_name']}")
                    print(f"   Page: {result['start_page']}")
                    print(f"   Snippet: {result['content_snippet']}")
                
                if results:
                    print("✅ FTS SEARCH WORKING - AI can search document content!")
                    
                    # Test more specific search
                    print(f"\n🔍 Testing specific search: 'safety PowerPress'...")
                    results2 = db_manager.execute_query(query, ("safety PowerPress",))
                    print(f"Found {len(results2)} matches for 'safety PowerPress'")
                    
                    print(f"\n🔍 Testing search: 'maintenance Tunnels'...")
                    results3 = db_manager.execute_query(query, ("maintenance Tunnels",))
                    print(f"Found {len(results3)} matches for 'maintenance Tunnels'")
                    
                    return True
                else:
                    print("❌ FTS search returned no results")
                    return False
            else:
                print("❌ No FTS tables found")
                return False
                
        except Exception as e:
            print(f"❌ FTS test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fts_search()
    if success:
        print(f"\n🎉 SUCCESS: AI has full content search capabilities!")
    else:
        print(f"\n❌ LIMITED: AI cannot search document content")