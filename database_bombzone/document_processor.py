#!/usr/bin/env python3
"""
Machine Document Processing System
Extracts, processes, and indexes machine documentation for AI-powered search.
"""

import os
import sqlite3
import hashlib
import mimetypes
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pickle

# PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Text processing and embeddings
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class DocumentProcessor:
    """Processes and indexes machine documentation files."""
    
    def __init__(self, database_path: str = "machine_docs.db", base_directory: str = None):
        """
        Initialize the document processor.
        
        Args:
            database_path: Path to SQLite database
            base_directory: Base directory for document files
        """
        self.database_path = database_path
        self.base_directory = Path(base_directory) if base_directory else Path(__file__).parent
        self.logger = self._setup_logging()
        
        # Initialize database
        self._init_database()
        
        # Initialize text processing
        self.stemmer = PorterStemmer() if NLTK_AVAILABLE else None
        self.stop_words = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
        
        # Initialize embedding model (lightweight, fast model)
        self.embedding_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("✅ Loaded sentence transformer model")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load embedding model: {e}")
        
        # Document type mapping based on file location
        self.document_type_mapping = {
            'operatingManuals': 'manual',
            'spareParts': 'parts',
            'Diagrams': 'diagram',
            'info': 'info',
            'subComponents': 'component',
            'generalDescription.txt': 'general',
            'Pinned Context': 'context'
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the processor."""
        logger = logging.getLogger('DocumentProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize the SQLite database with schema."""
        try:
            schema_path = self.base_directory / "schema.sql"
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                with sqlite3.connect(self.database_path) as conn:
                    conn.executescript(schema_sql)
                    conn.commit()
                
                self.logger.info(f"✅ Database initialized: {self.database_path}")
            else:
                self.logger.error(f"❌ Schema file not found: {schema_path}")
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
    
    def scan_and_index_all(self) -> Dict[str, Any]:
        """
        Scan the Machines directory and index all documents.
        
        Returns:
            Summary of processing results
        """
        self.logger.info("🔍 Starting full document scan and indexing...")
        
        machines_dir = self.base_directory / "Machines"
        if not machines_dir.exists():
            self.logger.error(f"❌ Machines directory not found: {machines_dir}")
            return {"error": "Machines directory not found"}
        
        results = {
            "machines_processed": 0,
            "documents_found": 0,
            "documents_processed": 0,
            "pages_extracted": 0,
            "chunks_created": 0,
            "errors": []
        }
        
        # Process each machine directory
        for machine_dir in machines_dir.iterdir():
            if machine_dir.is_dir():
                try:
                    machine_results = self._process_machine_directory(machine_dir)
                    results["machines_processed"] += 1
                    results["documents_found"] += machine_results.get("documents_found", 0)
                    results["documents_processed"] += machine_results.get("documents_processed", 0)
                    results["pages_extracted"] += machine_results.get("pages_extracted", 0)
                    results["chunks_created"] += machine_results.get("chunks_created", 0)
                    
                    if machine_results.get("errors"):
                        results["errors"].extend(machine_results["errors"])
                        
                except Exception as e:
                    error_msg = f"Error processing machine {machine_dir.name}: {e}"
                    self.logger.error(f"❌ {error_msg}")
                    results["errors"].append(error_msg)
        
        self.logger.info(f"✅ Indexing complete: {results}")
        return results
    
    def _process_machine_directory(self, machine_dir: Path) -> Dict[str, Any]:
        """Process a single machine directory."""
        machine_name = machine_dir.name
        self.logger.info(f"📂 Processing machine: {machine_name}")
        
        # Create or update machine record
        machine_id = self._ensure_machine_record(machine_dir)
        
        results = {
            "documents_found": 0,
            "documents_processed": 0,
            "pages_extracted": 0,
            "chunks_created": 0,
            "errors": []
        }
        
        # Recursively find all files
        for file_path in machine_dir.rglob("*"):
            if file_path.is_file():
                try:
                    results["documents_found"] += 1
                    
                    # Determine document type from path
                    doc_type = self._determine_document_type(file_path, machine_dir)
                    
                    # Process the document
                    doc_results = self._process_document(file_path, machine_id, doc_type)
                    
                    if doc_results["success"]:
                        results["documents_processed"] += 1
                        results["pages_extracted"] += doc_results.get("pages_extracted", 0)
                        results["chunks_created"] += doc_results.get("chunks_created", 0)
                    else:
                        results["errors"].append(doc_results.get("error", "Unknown error"))
                        
                except Exception as e:
                    error_msg = f"Error processing file {file_path}: {e}"
                    self.logger.error(f"❌ {error_msg}")
                    results["errors"].append(error_msg)
        
        return results
    
    def _ensure_machine_record(self, machine_dir: Path) -> int:
        """Create or update machine record in database."""
        machine_name = machine_dir.name
        
        # Try to extract additional machine info
        machine_info = self._extract_machine_info(machine_dir)
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Check if machine exists
            cursor.execute("SELECT id FROM machines WHERE machine_name = ?", (machine_name,))
            result = cursor.fetchone()
            
            if result:
                machine_id = result[0]
                # Update existing record
                cursor.execute("""
                    UPDATE machines 
                    SET machine_type = ?, line_number = ?, description = ?, 
                        directory_path = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    machine_info.get("machine_type"),
                    machine_info.get("line_number"),
                    machine_info.get("description"),
                    str(machine_dir.relative_to(self.base_directory)),
                    machine_id
                ))
            else:
                # Create new record
                cursor.execute("""
                    INSERT INTO machines (machine_name, machine_type, line_number, 
                                        description, directory_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    machine_name,
                    machine_info.get("machine_type"),
                    machine_info.get("line_number"), 
                    machine_info.get("description"),
                    str(machine_dir.relative_to(self.base_directory))
                ))
                machine_id = cursor.lastrowid
            
            conn.commit()
        
        return machine_id
    
    def _extract_machine_info(self, machine_dir: Path) -> Dict[str, str]:
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
                with open(desc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract first meaningful line as description
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    for line in lines:
                        if not line.startswith('#') and not line.startswith('Pinned Context'):
                            info["description"] = line[:200]  # Limit length
                            break
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read description file: {e}")
        
        return info
    
    def _determine_document_type(self, file_path: Path, machine_dir: Path) -> str:
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
            if part in self.document_type_mapping:
                return self.document_type_mapping[part]
        
        # Check file extension
        if file_path.suffix.lower() == '.pdf':
            # Try to infer from filename
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
    
    def _process_document(self, file_path: Path, machine_id: int, doc_type: str) -> Dict[str, Any]:
        """Process a single document file."""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Check if document already processed with same hash
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, is_processed FROM documents 
                    WHERE file_path = ? AND content_hash = ?
                """, (str(file_path.relative_to(self.base_directory)), file_hash))
                result = cursor.fetchone()
                
                if result and result[1]:  # Already processed
                    return {"success": True, "message": "Already processed", "document_id": result[0]}
            
            # Create/update document record
            document_id = self._create_document_record(file_path, machine_id, doc_type, file_hash)
            
            # Extract content based on file type
            if file_path.suffix.lower() == '.pdf' and PDF_AVAILABLE:
                return self._process_pdf_document(file_path, document_id)
            elif file_path.suffix.lower() == '.txt':
                return self._process_text_document(file_path, document_id)
            else:
                return {"success": False, "error": f"Unsupported file type: {file_path.suffix}"}
                
        except Exception as e:
            self.logger.error(f"❌ Error processing document {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _create_document_record(self, file_path: Path, machine_id: int, doc_type: str, file_hash: str) -> int:
        """Create or update document record in database."""
        relative_path = str(file_path.relative_to(self.base_directory))
        file_stats = file_path.stat()
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Try to update existing record
            cursor.execute("""
                UPDATE documents 
                SET content_hash = ?, file_size = ?, document_type = ?, 
                    is_processed = FALSE, processing_status = 'pending',
                    updated_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
            """, (file_hash, file_stats.st_size, doc_type, relative_path))
            
            if cursor.rowcount == 0:
                # Create new record
                cursor.execute("""
                    INSERT INTO documents 
                    (machine_id, file_path, filename, document_type, file_extension,
                     content_hash, file_size, is_processed, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, 'pending')
                """, (
                    machine_id, relative_path, file_path.name, doc_type,
                    file_path.suffix, file_hash, file_stats.st_size
                ))
                document_id = cursor.lastrowid
            else:
                # Get existing document ID
                cursor.execute("SELECT id FROM documents WHERE file_path = ?", (relative_path,))
                document_id = cursor.fetchone()[0]
            
            conn.commit()
        
        return document_id
    
    def _process_pdf_document(self, file_path: Path, document_id: int) -> Dict[str, Any]:
        """Process a PDF document."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                self._update_document_status(document_id, 'processing', f"Extracting {total_pages} pages")
                
                pages_processed = 0
                chunks_created = 0
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        # Extract text from page
                        text = page.extract_text()
                        
                        if text.strip():  # Only process pages with text
                            # Clean and process text
                            cleaned_text = self._clean_text(text)
                            
                            # Create page record
                            page_id = self._create_page_record(document_id, page_num, text, cleaned_text)
                            
                            # Create content chunks
                            chunks = self._create_content_chunks(document_id, page_num, cleaned_text)
                            chunks_created += len(chunks)
                            
                            pages_processed += 1
                    
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error processing page {page_num}: {e}")
                
                # Update document as processed
                self._update_document_record(document_id, total_pages, "PDF processing completed")
                
                return {
                    "success": True,
                    "document_id": document_id,
                    "pages_extracted": pages_processed,
                    "chunks_created": chunks_created
                }
                
        except Exception as e:
            self._update_document_status(document_id, 'failed', str(e))
            return {"success": False, "error": str(e)}
    
    def _process_text_document(self, file_path: Path, document_id: int) -> Dict[str, Any]:
        """Process a text document."""
        try:
            self._update_document_status(document_id, 'processing', "Processing text file")
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            if content.strip():
                # Clean text
                cleaned_text = self._clean_text(content)
                
                # Create single page record
                page_id = self._create_page_record(document_id, 1, content, cleaned_text)
                
                # Create content chunks
                chunks = self._create_content_chunks(document_id, 1, cleaned_text)
                
                # Update document as processed
                self._update_document_record(document_id, 1, "Text processing completed")
                
                return {
                    "success": True,
                    "document_id": document_id,
                    "pages_extracted": 1,
                    "chunks_created": len(chunks)
                }
            else:
                self._update_document_status(document_id, 'completed', "Empty file")
                return {"success": True, "document_id": document_id, "pages_extracted": 0, "chunks_created": 0}
                
        except Exception as e:
            self._update_document_status(document_id, 'failed', str(e))
            return {"success": False, "error": str(e)}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Basic text cleaning
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)\[\]\"\'\/\\]', '', text)  # Remove special chars
        text = text.strip()
        
        return text
    
    def _create_page_record(self, document_id: int, page_number: int, 
                          raw_text: str, cleaned_text: str) -> int:
        """Create a page record in the database."""
        # Extract keywords
        keywords = self._extract_keywords(cleaned_text)
        word_count = len(cleaned_text.split())
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO document_pages 
                (document_id, page_number, content_text, content_cleaned, 
                 keywords, word_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                document_id, page_number, raw_text, cleaned_text,
                ','.join(keywords), word_count
            ))
            
            page_id = cursor.lastrowid
            conn.commit()
        
        return page_id
    
    def _create_content_chunks(self, document_id: int, page_number: int, 
                             text: str) -> List[int]:
        """Create content chunks for semantic search."""
        chunks = []
        chunk_size = 800  # Target chunk size in words
        overlap = 100     # Word overlap between chunks
        
        words = text.split()
        
        if len(words) <= chunk_size:
            # Small text - create single chunk
            chunks.append(text)
        else:
            # Split into overlapping chunks
            start = 0
            chunk_index = 0
            
            while start < len(words):
                end = min(start + chunk_size, len(words))
                chunk_words = words[start:end]
                chunk_text = ' '.join(chunk_words)
                
                chunks.append(chunk_text)
                
                # Move start position with overlap
                start = end - overlap
                if start >= len(words) - overlap:
                    break
                
                chunk_index += 1
        
        # Store chunks in database
        chunk_ids = []
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            for i, chunk_text in enumerate(chunks):
                # Extract keywords for chunk
                keywords = self._extract_keywords(chunk_text)
                word_count = len(chunk_text.split())
                
                # Generate embedding if model available
                embedding_blob = None
                if self.embedding_model:
                    try:
                        embedding = self.embedding_model.encode(chunk_text)
                        embedding_blob = pickle.dumps(embedding)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to generate embedding: {e}")
                
                cursor.execute("""
                    INSERT INTO content_chunks 
                    (document_id, page_number, chunk_index, chunk_text, 
                     keywords, word_count, embedding_vector)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_id, page_number, i, chunk_text,
                    ','.join(keywords), word_count, embedding_blob
                ))
                
                chunk_ids.append(cursor.lastrowid)
            
            conn.commit()
        
        return chunk_ids
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        if not NLTK_AVAILABLE:
            # Simple keyword extraction without NLTK
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            return list(set(words[:20]))  # Return unique words, limit to 20
        
        # Tokenize and clean
        words = word_tokenize(text.lower())
        
        # Filter out stop words and short words
        keywords = [
            self.stemmer.stem(word) if self.stemmer else word 
            for word in words 
            if word.isalpha() and len(word) > 2 and word not in self.stop_words
        ]
        
        # Get unique keywords, sorted by frequency
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Return top keywords
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [kw[0] for kw in sorted_keywords[:20]]
    
    def _update_document_status(self, document_id: int, status: str, message: str = None):
        """Update document processing status."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET processing_status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, document_id))
            
            # Log the status update
            cursor.execute("""
                INSERT INTO processing_logs (document_id, operation, status, message)
                VALUES (?, 'process', ?, ?)
            """, (document_id, status, message))
            
            conn.commit()
    
    def _update_document_record(self, document_id: int, page_count: int, message: str):
        """Mark document as processed and update metadata."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET is_processed = TRUE, processing_status = 'completed', 
                    page_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (page_count, document_id))
            
            # Log completion
            cursor.execute("""
                INSERT INTO processing_logs (document_id, operation, status, message)
                VALUES (?, 'complete', 'completed', ?)
            """, (document_id, message))
            
            conn.commit()
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Get overall statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN is_processed = 1 THEN 1 END) as processed_documents,
                    COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed_documents,
                    SUM(page_count) as total_pages
                FROM documents
            """)
            
            stats = cursor.fetchone()
            
            # Get machine summary
            cursor.execute("SELECT * FROM machine_document_summary")
            machine_summary = cursor.fetchall()
            
            # Get recent processing logs
            cursor.execute("""
                SELECT pl.created_at, d.filename, pl.operation, pl.status, pl.message
                FROM processing_logs pl
                JOIN documents d ON pl.document_id = d.id
                ORDER BY pl.created_at DESC
                LIMIT 10
            """)
            recent_logs = cursor.fetchall()
        
        return {
            "total_documents": stats[0],
            "processed_documents": stats[1], 
            "failed_documents": stats[2],
            "total_pages": stats[3] or 0,
            "machine_summary": machine_summary,
            "recent_logs": recent_logs
        }


if __name__ == "__main__":
    # Example usage
    processor = DocumentProcessor(
        database_path="machine_docs.db",
        base_directory="/root/fixxitV2/database_bombzone"
    )
    
    print("🚀 Starting document processing...")
    results = processor.scan_and_index_all()
    print(f"✅ Processing complete: {results}")
    
    print("\n📊 Final status:")
    status = processor.get_processing_status()
    print(json.dumps(status, indent=2, default=str))