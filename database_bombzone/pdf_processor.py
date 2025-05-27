#!/usr/bin/env python3
"""
Lightweight PDF processor using available system libraries
"""
import sqlite3
import os
import subprocess
from pathlib import Path

def extract_pdf_text_with_pdftotext(pdf_path):
    """Extract text from PDF using pdftotext command line tool"""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"pdftotext error for {pdf_path}: {result.stderr}")
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

def extract_pdf_text_with_python():
    """Try to import and use PyPDF2 if available"""
    try:
        import PyPDF2
        def extract_text(pdf_path):
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        return extract_text
    except ImportError:
        return None

def process_pdfs_in_database(db_path):
    """Process all unprocessed PDF files in the database"""
    
    # Try to get a PDF text extractor
    python_extractor = extract_pdf_text_with_python()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get all unprocessed PDF documents
        cursor.execute("""
            SELECT id, file_path, machine_id 
            FROM documents 
            WHERE file_path LIKE '%.pdf' AND is_processed = FALSE
        """)
        
        pdf_docs = cursor.fetchall()
        print(f"Found {len(pdf_docs)} PDF files to process")
        
        processed_count = 0
        failed_count = 0
        
        for doc_id, file_path, machine_id in pdf_docs:
            try:
                print(f"Processing: {Path(file_path).name}")
                
                text_content = None
                
                # Try PyPDF2 first if available
                if python_extractor and Path(file_path).exists():
                    try:
                        text_content = python_extractor(file_path)
                    except Exception as e:
                        print(f"PyPDF2 failed for {file_path}: {e}")
                
                # Fall back to pdftotext if PyPDF2 failed or unavailable
                if not text_content and Path(file_path).exists():
                    text_content = extract_pdf_text_with_pdftotext(file_path)
                
                if text_content and text_content.strip():
                    # Split into pages (rough estimation)
                    pages = text_content.split('\f')  # Form feed character often separates pages
                    if len(pages) == 1:
                        # If no form feeds, split by reasonable chunk size
                        words = text_content.split()
                        page_size = max(500, len(words) // 5)  # Estimate 5 pages max
                        pages = [' '.join(words[i:i+page_size]) for i in range(0, len(words), page_size)]
                    
                    # Insert pages into database
                    for page_num, page_text in enumerate(pages, 1):
                        if page_text.strip():
                            cursor.execute("""
                                INSERT INTO document_pages (document_id, page_number, text_content, word_count)
                                VALUES (?, ?, ?, ?)
                            """, (doc_id, page_num, page_text.strip(), len(page_text.split())))
                    
                    # Mark document as processed
                    cursor.execute("""
                        UPDATE documents SET is_processed = TRUE WHERE id = ?
                    """, (doc_id,))
                    
                    processed_count += 1
                    print(f"  ✅ Extracted {len(pages)} pages")
                    
                else:
                    print(f"  ❌ Could not extract text from {file_path}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error processing {file_path}: {e}")
                failed_count += 1
        
        conn.commit()
        
        print(f"\n📊 PDF Processing Summary:")
        print(f"   Successfully processed: {processed_count}")
        print(f"   Failed: {failed_count}")
        print(f"   Total PDFs: {len(pdf_docs)}")

if __name__ == "__main__":
    db_path = "machine_docs.db"
    if not os.path.exists(db_path):
        print("Database not found. Run process_files.py first.")
        exit(1)
    
    process_pdfs_in_database(db_path)