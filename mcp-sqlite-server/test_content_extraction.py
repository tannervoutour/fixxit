#!/usr/bin/env python3
"""Test document content extraction capabilities."""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_content_extraction():
    """Test if actual document content is stored and accessible."""
    
    print("🧪 Testing Document Content Extraction")
    print("=" * 50)
    
    try:
        from utils.db_connection import db_manager
        print("✅ Database connection ready")
        
        # Check if sections have content_text
        print("\n📋 Checking document_sections table structure...")
        schema = db_manager.get_table_schema("document_sections")
        content_columns = [col for col in schema if 'content' in col['name'].lower()]
        
        print(f"Content-related columns: {[col['name'] for col in content_columns]}")
        
        # Check for Tunnels sections with content
        print("\n📋 Checking Tunnels machine sections...")
        sections_query = """
            SELECT ds.section_name, ds.section_title, ds.start_page, ds.word_count,
                   LENGTH(ds.content_text) as content_length,
                   SUBSTR(ds.content_text, 1, 200) as content_preview
            FROM document_sections ds
            JOIN machines m ON ds.machine_id = m.id
            WHERE m.machine_name = 'Tunnels'
            ORDER BY ds.section_order
            LIMIT 5
        """
        
        sections = db_manager.execute_query(sections_query)
        print(f"Found {len(sections)} sections for Tunnels")
        
        for section in sections:
            print(f"\n📄 Section: {section['section_name']}")
            print(f"   Title: {section['section_title']}")
            print(f"   Page: {section['start_page']}")
            print(f"   Words: {section['word_count']}")
            print(f"   Content length: {section['content_length']} characters")
            
            if section['content_length'] and section['content_length'] > 0:
                print(f"   Preview: {section['content_preview']}...")
                print("   ✅ HAS ACTUAL CONTENT")
            else:
                print("   ❌ NO CONTENT STORED")
        
        # Test the get_section_content function specifically
        print(f"\n📋 Testing get_section_content function...")
        
        def test_get_section_content(machine_name, section_name, document_filename=None):
            """Test version of get_section_content."""
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
        
        # Test getting safety content for Tunnels
        print("🧪 Testing content extraction for 'Tunnels' + 'Safety'...")
        result = test_get_section_content("Tunnels", "Safety")
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Section: {result['section_name']}")
            print(f"Title: {result['section_title']}")
            print(f"Pages: {result['start_page']}-{result['end_page']}")
            print(f"Word count: {result['word_count']}")
            
            content = result['content']
            if content and len(content) > 0:
                print(f"Content length: {len(content)} characters")
                print(f"Content preview (first 300 chars):")
                print("-" * 40)
                print(content[:300] + "..." if len(content) > 300 else content)
                print("-" * 40)
                print("✅ AI CAN EXTRACT ACTUAL DOCUMENT CONTENT!")
                return True
            else:
                print("❌ No content in section")
                return False
        else:
            print(f"Error: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_content_extraction()
    if success:
        print(f"\n🎉 SUCCESS: AI can extract actual document content with page references!")
    else:
        print(f"\n❌ LIMITED: AI can only access metadata, not full content")