#!/usr/bin/env python3
"""
Complete Document Processing Pipeline
Processes machine manuals and populates the documentation database.
"""

import os
import re
import sys
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import json
from datetime import datetime

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    print("❌ PyPDF2 not available. Install with: pip install PyPDF2")
    sys.exit(1)

class DocumentProcessor:
    """Complete document processing pipeline for machine manuals."""
    
    def __init__(self, 
                 machines_dir: str = "/root/fixxitV2/Machines",
                 database_path: str = "/root/fixxitV2/mcp-sqlite-server/database/database.db"):
        self.machines_dir = Path(machines_dir)
        self.database_path = database_path
        self.logger = self._setup_logging()
        
        # Section patterns for better TOC parsing
        self.toc_patterns = [
            # Enhanced TOC line patterns
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][^.]+?)\.?\s*\.+\s*(\d+)',  # "1.1 Safety .... 5"
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][^.]+?)\s+(\d+)\s*$',       # "1.1 Safety 5"
            r'^\s*(\d+)\.\s*([A-Z][^.]+?)\s*\.+\s*(\d+)',            # "1. Safety .... 5"
            r'^\s*([A-Z][A-Z\s]+?)\s*\.+\s*(\d+)',                   # "SAFETY .... 5"
            r'^\s*(\d+\.?\d*)\s+([A-Z][\w\s-]+?)\s+(\d+)$',          # "1.1 Safety Instructions 5"
        ]
        
        # Content header patterns for fallback
        self.header_patterns = [
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][A-Z\s]+)',                 # "1.1 SAFETY PROCEDURES"
            r'^\s*([A-Z][A-Z\s]{4,})\s*$',                           # "SAFETY PROCEDURES"
            r'^\s*(\d+)\.\s*([A-Z][A-Z\s]+)',                        # "1. SAFETY PROCEDURES"
        ]
        
        # Common section name patterns for classification
        self.section_types = {
            'safety': r'(?i)(safety|warning|caution|danger)',
            'operation': r'(?i)(operation|operating|procedure|startup|shutdown)',
            'maintenance': r'(?i)(maintenance|service|cleaning|lubrication)',
            'troubleshooting': r'(?i)(troubleshooting|fault|error|problem|diagnostic)',
            'installation': r'(?i)(installation|setup|assembly|mounting)',
            'specifications': r'(?i)(specification|technical|dimension|capacity)',
            'parts': r'(?i)(parts|component|spare|replacement)',
        }
    
    def _setup_logging(self):
        """Setup logging for the processor."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _ensure_database_connection(self):
        """Ensure database exists and is accessible."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM machines")
                return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _extract_machine_info(self, machine_dir: Path) -> Dict[str, str]:
        """Extract machine information from directory structure."""
        machine_name = machine_dir.name
        info = {
            "machine_name": machine_name,
            "machine_type": None,
            "line_number": None,
            "sub_machine": None,
            "description": None,
            "directory_path": str(machine_dir.relative_to(self.machines_dir.parent))
        }
        
        # Handle Line_X machines (which contain sub-machines)
        if machine_name.startswith("Line_"):
            info["line_number"] = machine_name
            
            # Look for sub-machine directories
            for sub_dir in machine_dir.iterdir():
                if sub_dir.is_dir() and sub_dir.name in ["Feeder", "Folder", "Ironer"]:
                    # For Line machines, we'll create entries for each sub-machine
                    pass
        else:
            # Extract line number from path if present
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
            'xfm': 'folder',
            'steam': 'steamer'
        }
        
        for keyword, machine_type in type_mapping.items():
            if keyword.lower() in machine_name.lower():
                info["machine_type"] = machine_type
                break
        
        # Try to read description from general description file
        desc_files = [
            machine_dir / f"{machine_name}-generalDescription.txt",
            machine_dir / f"{machine_name} -generalDescription.txt"
        ]
        
        for desc_file in desc_files:
            if desc_file.exists():
                try:
                    with open(desc_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        for line in lines:
                            if not line.startswith('#') and not line.startswith('Pinned Context'):
                                info["description"] = line[:200]  # Limit length
                                break
                except Exception as e:
                    self.logger.warning(f"Could not read description file: {e}")
                break
        
        return info
    
    def _create_machine_record(self, machine_info: Dict[str, str]) -> int:
        """Create or update machine record in database."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Check if machine exists
            cursor.execute("SELECT id FROM machines WHERE machine_name = ?", (machine_info["machine_name"],))
            result = cursor.fetchone()
            
            if result:
                machine_id = result[0]
                # Update existing record
                cursor.execute("""
                    UPDATE machines 
                    SET machine_type = ?, line_number = ?, sub_machine = ?, 
                        description = ?, directory_path = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    machine_info["machine_type"],
                    machine_info["line_number"],
                    machine_info["sub_machine"],
                    machine_info["description"],
                    machine_info["directory_path"],
                    machine_id
                ))
            else:
                # Create new record
                cursor.execute("""
                    INSERT INTO machines (machine_name, machine_type, line_number, sub_machine,
                                        description, directory_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    machine_info["machine_name"],
                    machine_info["machine_type"],
                    machine_info["line_number"], 
                    machine_info["sub_machine"],
                    machine_info["description"],
                    machine_info["directory_path"]
                ))
                machine_id = cursor.lastrowid
            
            conn.commit()
        
        return machine_id
    
    def _find_operating_manuals(self, machine_dir: Path) -> List[Path]:
        """Find operating manual PDFs for a machine."""
        manuals = []
        
        # Look in operatingManuals subdirectory
        operating_dir = machine_dir / "operatingManuals"
        if operating_dir.exists():
            for pdf_file in operating_dir.glob("*.pdf"):
                manuals.append(pdf_file)
        
        # Also check root directory for any manual PDFs
        for pdf_file in machine_dir.glob("*.pdf"):
            if any(keyword in pdf_file.name.lower() for keyword in ['operating', 'manual', 'instruction']):
                manuals.append(pdf_file)
        
        return manuals
    
    def _extract_pdf_pages(self, pdf_path: Path) -> Dict[int, str]:
        """Extract text from PDF by page."""
        pages = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            pages[page_num] = text
                    except Exception as e:
                        self.logger.warning(f"Error reading page {page_num}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error reading PDF {pdf_path}: {e}")
            
        return pages
    
    def _find_table_of_contents(self, pages: Dict[int, str]) -> Optional[Tuple[int, str]]:
        """Find the table of contents page."""
        toc_keywords = [
            r'(?i)table\s+of\s+contents',
            r'(?i)^contents\s*$',
            r'(?i)index'
        ]
        
        for page_num, text in pages.items():
            if page_num > 10:  # Don't search beyond page 10
                break
                
            lines = text.split('\n')
            for line in lines[:20]:  # Check first 20 lines
                for pattern in toc_keywords:
                    if re.search(pattern, line.strip()):
                        return page_num, text
        
        return None
    
    def _parse_toc_sections(self, toc_text: str) -> List[Dict[str, any]]:
        """Parse table of contents to extract sections."""
        sections = []
        lines = toc_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
                
            for pattern in self.toc_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        section_num, section_name, page_num = groups
                        try:
                            sections.append({
                                'section_number': section_num.strip(),
                                'section_name': section_name.strip(),
                                'start_page': int(page_num),
                                'raw_line': line
                            })
                        except ValueError:
                            continue
                    elif len(groups) == 2:
                        section_name, page_num = groups
                        try:
                            sections.append({
                                'section_number': '',
                                'section_name': section_name.strip(),
                                'start_page': int(page_num),
                                'raw_line': line
                            })
                        except ValueError:
                            continue
                    break
        
        # Sort by start page
        sections.sort(key=lambda x: x['start_page'])
        
        # Calculate end pages
        for i, section in enumerate(sections):
            if i < len(sections) - 1:
                section['end_page'] = sections[i + 1]['start_page'] - 1
            else:
                section['end_page'] = None  # Last section goes to end of document
        
        return sections
    
    def _extract_section_content(self, pages: Dict[int, str], section: Dict[str, any]) -> str:
        """Extract content for a specific section."""
        content_parts = []
        start_page = section['start_page']
        end_page = section.get('end_page', max(pages.keys()))
        
        for page_num in range(start_page, (end_page or max(pages.keys())) + 1):
            if page_num in pages:
                page_text = pages[page_num]
                # Clean the text
                cleaned_text = re.sub(r'\s+', ' ', page_text).strip()
                content_parts.append(cleaned_text)
        
        return ' '.join(content_parts)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter common words and get unique keywords
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        keywords = [word for word in set(words) if len(word) > 3 and word not in common_words]
        return sorted(keywords)[:20]  # Return top 20
    
    def _classify_section_type(self, section_name: str) -> str:
        """Classify section type based on name."""
        section_name_lower = section_name.lower()
        
        for section_type, pattern in self.section_types.items():
            if re.search(pattern, section_name_lower):
                return section_type
        
        return 'general'
    
    def _create_document_record(self, file_path: Path, machine_id: int) -> int:
        """Create document record in database."""
        relative_path = str(file_path.relative_to(self.machines_dir.parent))
        file_hash = self._calculate_file_hash(file_path)
        file_stats = file_path.stat()
        
        # Extract total page count
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
        except:
            page_count = 1
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Check if document already exists
            cursor.execute("SELECT id FROM documents WHERE file_path = ?", (relative_path,))
            result = cursor.fetchone()
            
            if result:
                document_id = result[0]
                # Update existing
                cursor.execute("""
                    UPDATE documents 
                    SET content_hash = ?, file_size = ?, page_count = ?, 
                        is_processed = FALSE, processing_status = 'pending',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (file_hash, file_stats.st_size, page_count, document_id))
            else:
                # Create new
                cursor.execute("""
                    INSERT INTO documents 
                    (machine_id, file_path, filename, document_type, file_extension,
                     content_hash, file_size, page_count, is_processed, processing_status)
                    VALUES (?, ?, ?, 'manual', ?, ?, ?, ?, FALSE, 'pending')
                """, (
                    machine_id, relative_path, file_path.name, file_path.suffix,
                    file_hash, file_stats.st_size, page_count
                ))
                document_id = cursor.lastrowid
            
            conn.commit()
        
        return document_id
    
    def _create_section_records(self, document_id: int, machine_id: int, sections: List[Dict], pages: Dict[int, str]):
        """Create section records in database."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing sections for this document
            cursor.execute("DELETE FROM document_sections WHERE document_id = ?", (document_id,))
            
            for i, section in enumerate(sections):
                # Extract section content
                content = self._extract_section_content(pages, section)
                keywords = self._extract_keywords(content)
                word_count = len(content.split())
                
                cursor.execute("""
                    INSERT INTO document_sections 
                    (document_id, machine_id, section_name, section_title, 
                     start_page, end_page, content_text, keywords, word_count, section_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_id, machine_id, section['section_name'], 
                    section['section_name'], section['start_page'], 
                    section.get('end_page'), content,
                    ','.join(keywords), word_count, i
                ))
            
            conn.commit()
    
    def _mark_document_processed(self, document_id: int, section_count: int):
        """Mark document as processed."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET is_processed = TRUE, processing_status = 'completed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (document_id,))
            
            cursor.execute("""
                INSERT INTO processing_logs (document_id, operation, status, message)
                VALUES (?, 'process', 'completed', ?)
            """, (document_id, f"Extracted {section_count} sections"))
            
            conn.commit()
    
    def process_machine_directory(self, machine_dir: Path) -> Dict[str, any]:
        """Process a single machine directory."""
        machine_name = machine_dir.name
        self.logger.info(f"📂 Processing machine: {machine_name}")
        
        result = {
            "machine_name": machine_name,
            "success": False,
            "documents_processed": 0,
            "sections_extracted": 0,
            "errors": []
        }
        
        try:
            # Extract machine info and create record
            machine_info = self._extract_machine_info(machine_dir)
            machine_id = self._create_machine_record(machine_info)
            
            # Handle special case for Line machines
            if machine_name.startswith("Line_"):
                # Process sub-machines within the line
                sub_machine_dirs = [d for d in machine_dir.iterdir() if d.is_dir() and d.name in ["Feeder", "Folder", "Ironer"]]
                
                for sub_dir in sub_machine_dirs:
                    sub_machine_info = machine_info.copy()
                    sub_machine_info["machine_name"] = f"{machine_name}_{sub_dir.name}"
                    sub_machine_info["sub_machine"] = sub_dir.name
                    sub_machine_info["directory_path"] = str(sub_dir.relative_to(self.machines_dir.parent))
                    
                    sub_machine_id = self._create_machine_record(sub_machine_info)
                    
                    # Process manuals for sub-machine
                    manuals = self._find_operating_manuals(sub_dir)
                    for manual_path in manuals:
                        doc_result = self._process_single_document(manual_path, sub_machine_id)
                        if doc_result["success"]:
                            result["documents_processed"] += 1
                            result["sections_extracted"] += doc_result["sections_extracted"]
                        else:
                            result["errors"].append(doc_result["error"])
            
            # Process manuals for main machine
            manuals = self._find_operating_manuals(machine_dir)
            for manual_path in manuals:
                doc_result = self._process_single_document(manual_path, machine_id)
                if doc_result["success"]:
                    result["documents_processed"] += 1
                    result["sections_extracted"] += doc_result["sections_extracted"]
                else:
                    result["errors"].append(doc_result["error"])
            
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"Error processing machine {machine_name}: {e}")
        
        return result
    
    def _process_single_document(self, pdf_path: Path, machine_id: int) -> Dict[str, any]:
        """Process a single PDF document."""
        self.logger.info(f"📄 Processing: {pdf_path.name}")
        
        result = {
            "success": False,
            "sections_extracted": 0,
            "error": None
        }
        
        try:
            # Create document record
            document_id = self._create_document_record(pdf_path, machine_id)
            
            # Extract pages
            pages = self._extract_pdf_pages(pdf_path)
            if not pages:
                result["error"] = "No text extracted from PDF"
                return result
            
            # Find and parse table of contents
            toc_result = self._find_table_of_contents(pages)
            sections = []
            
            if toc_result:
                toc_page, toc_text = toc_result
                sections = self._parse_toc_sections(toc_text)
                self.logger.info(f"✅ Found {len(sections)} sections from TOC")
            
            # If no sections found, create a single section for the whole document
            if not sections:
                sections = [{
                    'section_number': '1',
                    'section_name': 'Complete Manual',
                    'start_page': 1,
                    'end_page': max(pages.keys()) if pages else 1
                }]
                self.logger.info("📖 No TOC found, treating as single section")
            
            # Create section records
            self._create_section_records(document_id, machine_id, sections, pages)
            
            # Mark as processed
            self._mark_document_processed(document_id, len(sections))
            
            result["success"] = True
            result["sections_extracted"] = len(sections)
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Error processing {pdf_path.name}: {e}")
        
        return result
    
    def process_all_machines(self) -> Dict[str, any]:
        """Process all machine directories."""
        self.logger.info("🚀 Starting complete documentation processing...")
        
        if not self._ensure_database_connection():
            return {"error": "Database connection failed"}
        
        if not self.machines_dir.exists():
            return {"error": f"Machines directory not found: {self.machines_dir}"}
        
        results = {
            "machines_processed": 0,
            "documents_processed": 0,
            "sections_extracted": 0,
            "errors": [],
            "processing_summary": []
        }
        
        # Process each machine directory
        for machine_dir in self.machines_dir.iterdir():
            if machine_dir.is_dir():
                machine_result = self.process_machine_directory(machine_dir)
                
                results["machines_processed"] += 1
                results["documents_processed"] += machine_result["documents_processed"]
                results["sections_extracted"] += machine_result["sections_extracted"]
                results["errors"].extend(machine_result["errors"])
                results["processing_summary"].append({
                    "machine": machine_result["machine_name"],
                    "documents": machine_result["documents_processed"],
                    "sections": machine_result["sections_extracted"],
                    "success": machine_result["success"]
                })
                
                self.logger.info(f"✅ {machine_result['machine_name']}: {machine_result['documents_processed']} docs, {machine_result['sections_extracted']} sections")
        
        self.logger.info(f"🎯 Processing complete: {results['machines_processed']} machines, {results['documents_processed']} documents, {results['sections_extracted']} sections")
        
        return results


def main():
    """Run the complete document processing pipeline."""
    processor = DocumentProcessor()
    
    print("🚀 Starting Machine Documentation Processing Pipeline")
    print("=" * 60)
    
    results = processor.process_all_machines()
    
    if "error" in results:
        print(f"❌ Processing failed: {results['error']}")
        return 1
    
    print("\n📊 PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Machines processed: {results['machines_processed']}")
    print(f"Documents processed: {results['documents_processed']}")
    print(f"Sections extracted: {results['sections_extracted']}")
    print(f"Errors encountered: {len(results['errors'])}")
    
    if results['errors']:
        print("\n⚠️ ERRORS:")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    print("\n📋 BY MACHINE:")
    for summary in results['processing_summary']:
        status = "✅" if summary['success'] else "❌"
        print(f"  {status} {summary['machine']}: {summary['documents']} docs, {summary['sections']} sections")
    
    print(f"\n✅ Documentation database ready for AI queries!")
    return 0


if __name__ == "__main__":
    sys.exit(main())