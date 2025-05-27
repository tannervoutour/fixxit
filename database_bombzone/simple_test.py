#!/usr/bin/env python3
"""
Simple test of the document database system without heavy dependencies.
"""

import os
import sqlite3
import sys
from pathlib import Path

def test_basic_functionality():
    """Test basic database and processing functionality."""
    print("🧪 Testing Machine Documentation Database System")
    print("=" * 60)
    
    # Check if schema file exists
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        print("❌ Schema file not found")
        return False
    
    print("✅ Schema file found")
    
    # Test database creation
    db_path = Path(__file__).parent / "test_machine_docs.db"
    
    try:
        # Remove existing test database
        if db_path.exists():
            db_path.unlink()
        
        # Create database with schema
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.executescript(schema_sql)
            conn.commit()
        
        print("✅ Database created successfully")
        
        # Test basic inserts
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Insert a test machine
            cursor.execute("""
                INSERT INTO machines (machine_name, machine_type, line_number, description)
                VALUES (?, ?, ?, ?)
            """, ("CSP", "separator", "General", "Test separator machine"))
            
            machine_id = cursor.lastrowid
            
            # Insert a test document
            cursor.execute("""
                INSERT INTO documents (machine_id, file_path, filename, document_type, 
                                     file_extension, content_hash, file_size, is_processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (machine_id, "test/path.txt", "test.txt", "general", ".txt", 
                  "testhash", 1024, True))
            
            doc_id = cursor.lastrowid
            
            # Insert test page content
            cursor.execute("""
                INSERT INTO document_pages (document_id, page_number, content_text, 
                                          content_cleaned, keywords, word_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, 1, "Test content", "Test content", "test,content", 2))
            
            conn.commit()
        
        print("✅ Test data inserted successfully")
        
        # Test basic queries
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Test machine summary view
            cursor.execute("SELECT * FROM machine_document_summary")
            results = cursor.fetchall()
            print(f"✅ Machine summary query returned {len(results)} results")
            
            # Test document search simulation
            cursor.execute("""
                SELECT m.machine_name, d.filename, dp.content_cleaned
                FROM machines m
                JOIN documents d ON m.id = d.machine_id
                JOIN document_pages dp ON d.id = dp.document_id
                WHERE dp.content_cleaned LIKE ?
            """, ("%test%",))
            
            search_results = cursor.fetchall()
            print(f"✅ Basic search simulation returned {len(search_results)} results")
            
            if search_results:
                for result in search_results:
                    print(f"   Found: {result[0]}/{result[1]} - {result[2]}")
        
        # Clean up test database
        db_path.unlink()
        print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def check_machine_structure():
    """Check the Machines directory structure."""
    print("\n📂 Checking Machine Directory Structure")
    print("-" * 40)
    
    machines_dir = Path(__file__).parent / "Machines"
    if not machines_dir.exists():
        print("❌ Machines directory not found")
        return False
    
    print("✅ Machines directory found")
    
    machine_count = 0
    file_count = 0
    
    for machine_dir in machines_dir.iterdir():
        if machine_dir.is_dir():
            machine_count += 1
            print(f"📁 Machine: {machine_dir.name}")
            
            # Count files recursively
            machine_files = list(machine_dir.rglob("*"))
            machine_file_count = len([f for f in machine_files if f.is_file()])
            file_count += machine_file_count
            
            print(f"   📄 Files: {machine_file_count}")
            
            # Show document types
            doc_types = set()
            for file_path in machine_files:
                if file_path.is_file():
                    if "operatingManuals" in str(file_path):
                        doc_types.add("manual")
                    elif "spareParts" in str(file_path):
                        doc_types.add("parts")
                    elif "Diagrams" in str(file_path):
                        doc_types.add("diagram")
                    elif "Pinned Context" in file_path.name:
                        doc_types.add("context")
                    elif "generalDescription.txt" in file_path.name:
                        doc_types.add("general")
                    else:
                        doc_types.add("info")
            
            if doc_types:
                print(f"   📋 Document types: {', '.join(sorted(doc_types))}")
    
    print(f"\n📊 Summary:")
    print(f"   Machines: {machine_count}")
    print(f"   Total files: {file_count}")
    
    return machine_count > 0

def check_document_types():
    """Check what types of documents we have."""
    print("\n📋 Document Type Analysis")
    print("-" * 30)
    
    machines_dir = Path(__file__).parent / "Machines"
    
    pdf_count = 0
    txt_count = 0
    context_count = 0
    
    for file_path in machines_dir.rglob("*"):
        if file_path.is_file():
            if file_path.suffix.lower() == '.pdf':
                pdf_count += 1
            elif file_path.suffix.lower() == '.txt':
                txt_count += 1
            
            if "Pinned Context" in file_path.name:
                context_count += 1
    
    print(f"📄 PDF files: {pdf_count}")
    print(f"📝 Text files: {txt_count}")
    print(f"📌 Context files: {context_count}")
    
    # Show sample files
    print(f"\n📋 Sample files:")
    sample_count = 0
    for file_path in machines_dir.rglob("*"):
        if file_path.is_file() and sample_count < 5:
            rel_path = file_path.relative_to(machines_dir)
            print(f"   {rel_path}")
            sample_count += 1
    
    return True

def main():
    """Run all tests."""
    print("🏭 Machine Documentation Database - Simple Test")
    print("=" * 60)
    
    # Test basic functionality
    if not test_basic_functionality():
        print("❌ Basic functionality test failed")
        return False
    
    # Check machine structure  
    if not check_machine_structure():
        print("❌ Machine structure check failed")
        return False
    
    # Check document types
    if not check_document_types():
        print("❌ Document type check failed")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📝 Next steps:")
    print("1. Install dependencies: uv add PyPDF2 sentence-transformers")
    print("2. Run full setup: python setup_database.py")
    print("3. Test search: python document_search_tools.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)