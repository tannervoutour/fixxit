#!/usr/bin/env python3
"""
Process machine documentation files without heavy dependencies.
"""

import os
import sqlite3
import hashlib
import re
from pathlib import Path
from datetime import datetime

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of file content."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def determine_document_type(file_path, machine_dir):
    """Determine document type based on file path and name."""
    relative_path = file_path.relative_to(machine_dir)
    path_parts = relative_path.parts
    filename = file_path.name
    
    # Check for pinned context files
    if "Pinned Context" in filename:
        return "context"
    
    # Check for general description files
    if "generalDescription.txt" in filename:
        return "general"
    
    # Check directory-based types
    for part in path_parts:
        if part == "operatingManuals":
            return "manual"
        elif part == "spareParts":
            return "parts"
        elif part == "Diagrams":
            return "diagram"
        elif part == "info":
            return "info"
        elif part == "subComponents":
            return "component"
    
    # Check file extension
    if file_path.suffix.lower() == '.pdf':
        filename_lower = filename.lower()
        if any(word in filename_lower for word in ['operating', 'manual', 'instruction']):
            return "manual"
        elif any(word in filename_lower for word in ['spare', 'parts']):
            return "parts"
        elif any(word in filename_lower for word in ['wiring', 'diagram', 'pneumatic', 'hydraulic']):
            return "diagram"
        else:
            return "manual"  # Default for PDFs
    elif file_path.suffix.lower() == '.txt':
        return "info"
    else:
        return "info"  # Default

def extract_machine_info(machine_dir):
    """Extract machine information from directory structure and files."""
    machine_name = machine_dir.name
    info = {"machine_type": None, "line_number": None, "description": None}
    
    # Extract line number from path
    if "Line_" in str(machine_dir):
        line_match = re.search(r'Line_(\d+)', str(machine_dir))
        if line_match:
            info["line_number"] = f"Line_{line_match.group(1)}"
    
    # Infer machine type from name
    type_mapping = {
        'feeder': 'feeder',
        'folder': 'folder', 
        'ironer': 'ironer',
        'dryer': 'dryer',
        'press': 'press',
        'picker': 'picker',
        'csp': 'separator',
        'tunnel': 'washer',
        'conveyor': 'conveyor',
        'xfm': 'folder'
    }
    
    for keyword, machine_type in type_mapping.items():
        if keyword.lower() in machine_name.lower():
            info["machine_type"] = machine_type
            break
    
    # Try to read description from general description file
    desc_file = machine_dir / f"{machine_name}-generalDescription.txt"
    if desc_file.exists():
        try:
            with open(desc_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Extract first meaningful line as description
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                for line in lines:
                    if not line.startswith('#') and not line.startswith('Pinned Context'):
                        info["description"] = line[:200]  # Limit length
                        break
        except Exception as e:
            print(f"⚠️ Could not read description file: {e}")
    
    return info

def process_text_file(file_path):
    """Process a text file and extract content."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Clean text
        cleaned_content = re.sub(r'\s+', ' ', content).strip()
        
        # Extract basic keywords
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_content.lower())
        unique_words = list(set(words))[:20]  # Top 20 unique words
        
        return {
            "success": True,
            "content": content,
            "cleaned_content": cleaned_content,
            "keywords": unique_words,
            "word_count": len(cleaned_content.split())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_machine_directory(machine_dir, db_path):
    """Process a single machine directory."""
    machine_name = machine_dir.name
    print(f"📂 Processing machine: {machine_name}")
    
    # Skip .vs directory (Visual Studio)
    if machine_name.startswith('.'):
        print(f"   ⏭️ Skipping system directory: {machine_name}")
        return {"documents_processed": 0, "errors": []}
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get or create machine record
        machine_info = extract_machine_info(machine_dir)
        
        cursor.execute("SELECT id FROM machines WHERE machine_name = ?", (machine_name,))
        result = cursor.fetchone()
        
        if result:
            machine_id = result[0]
            cursor.execute("""
                UPDATE machines 
                SET machine_type = ?, line_number = ?, description = ?, 
                    directory_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                machine_info.get("machine_type"),
                machine_info.get("line_number"),
                machine_info.get("description"),
                str(machine_dir),
                machine_id
            ))
        else:
            cursor.execute("""
                INSERT INTO machines (machine_name, machine_type, line_number, 
                                    description, directory_path)
                VALUES (?, ?, ?, ?, ?)
            """, (
                machine_name,
                machine_info.get("machine_type"),
                machine_info.get("line_number"), 
                machine_info.get("description"),
                str(machine_dir)
            ))
            machine_id = cursor.lastrowid
        
        conn.commit()
    
    # Process all files in machine directory
    documents_processed = 0
    errors = []
    
    for file_path in machine_dir.rglob("*"):
        if file_path.is_file():
            try:
                # Determine document type
                doc_type = determine_document_type(file_path, machine_dir)
                
                # Calculate file hash
                file_hash = calculate_file_hash(file_path)
                file_stats = file_path.stat()
                
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Check if document already exists
                    relative_path = str(file_path)
                    cursor.execute("""
                        SELECT id FROM documents 
                        WHERE file_path = ? AND content_hash = ?
                    """, (relative_path, file_hash))
                    
                    existing = cursor.fetchone()
                    if existing:
                        continue  # Skip if already processed
                    
                    # Create document record
                    cursor.execute("""
                        INSERT OR REPLACE INTO documents 
                        (machine_id, file_path, filename, document_type, file_extension,
                         content_hash, file_size, is_processed, processing_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        machine_id, relative_path, file_path.name, doc_type,
                        file_path.suffix, file_hash, file_stats.st_size,
                        False, 'pending'
                    ))
                    
                    document_id = cursor.lastrowid
                    
                    # Process text files
                    if file_path.suffix.lower() == '.txt':
                        result = process_text_file(file_path)
                        
                        if result["success"]:
                            # Create page record
                            cursor.execute("""
                                INSERT INTO document_pages 
                                (document_id, page_number, content_text, content_cleaned, 
                                 keywords, word_count)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                document_id, 1, result["content"], 
                                result["cleaned_content"],
                                ','.join(result["keywords"]), 
                                result["word_count"]
                            ))
                            
                            # Update document as processed
                            cursor.execute("""
                                UPDATE documents 
                                SET is_processed = TRUE, processing_status = 'completed',
                                    page_count = 1, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (document_id,))
                            
                            documents_processed += 1
                    else:
                        # For PDF files, just record them for now
                        cursor.execute("""
                            UPDATE documents 
                            SET processing_status = 'pdf_pending'
                            WHERE id = ?
                        """, (document_id,))
                    
                    conn.commit()
                
            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                print(f"   ❌ {error_msg}")
                errors.append(error_msg)
    
    print(f"   ✅ Processed {documents_processed} text documents")
    return {"documents_processed": documents_processed, "errors": errors}

def main():
    """Process all machine directories."""
    print("🏭 Processing Machine Documentation Files")
    print("=" * 60)
    
    db_path = "machine_docs.db"
    machines_dir = Path("Machines")
    
    if not machines_dir.exists():
        print("❌ Machines directory not found")
        return False
    
    total_machines = 0
    total_documents = 0
    all_errors = []
    
    for machine_dir in machines_dir.iterdir():
        if machine_dir.is_dir():
            total_machines += 1
            result = process_machine_directory(machine_dir, db_path)
            total_documents += result["documents_processed"]
            all_errors.extend(result["errors"])
    
    # Get final statistics
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM machines")
        machine_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM documents WHERE is_processed = 1")
        processed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM document_pages")
        page_count = cursor.fetchone()[0]
    
    print("\n📊 Processing Summary:")
    print(f"   Machines in database: {machine_count}")
    print(f"   Total documents: {doc_count}")
    print(f"   Processed documents: {processed_count}")
    print(f"   Total pages: {page_count}")
    
    if all_errors:
        print(f"\n⚠️ {len(all_errors)} errors occurred (see details in logs)")
    
    print("\n✅ Basic processing complete!")
    print("📝 Note: PDF files are registered but require PyPDF2 for text extraction")
    print("🚀 Ready for search testing with text documents")
    
    return True

if __name__ == "__main__":
    main()