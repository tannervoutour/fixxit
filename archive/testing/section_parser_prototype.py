#!/usr/bin/env python3
"""
PDF Section Parser Prototype
Tests table of contents extraction and section identification accuracy.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    print("❌ PyPDF2 not available. Install with: pip install PyPDF2")
    sys.exit(1)

class SectionParser:
    """Prototype parser for extracting sections from machine manuals."""
    
    def __init__(self, machines_dir: str = "/root/fixxitV2/Machines"):
        self.machines_dir = Path(machines_dir)
        self.logger = self._setup_logging()
        
        # Common section patterns found in manuals
        self.section_patterns = [
            # Table of contents patterns
            r'(?i)table\s+of\s+contents',
            r'(?i)contents',
            r'(?i)index',
            
            # Section number patterns
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][^.]+?)\.?\s*\.+\s*(\d+)',  # "1.1 Safety .... 5"
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][^.]+?)\s+(\d+)',  # "1.1 Safety 5"
            r'^\s*(\d+)\.\s*([A-Z][^.]+?)\s*\.+\s*(\d+)',   # "1. Safety .... 5"
            
            # Section headers in content
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][A-Z\s]+)',        # "1.1 SAFETY PROCEDURES"
            r'^\s*([A-Z][A-Z\s]{3,})\s*$',                  # "SAFETY PROCEDURES"
            
            # Common manual sections
            r'(?i)safety|warning|caution',
            r'(?i)operation|operating|procedure',
            r'(?i)maintenance|service',
            r'(?i)troubleshooting|fault|error',
            r'(?i)installation|setup',
            r'(?i)specification|technical',
            r'(?i)parts|components|spare',
        ]
    
    def _setup_logging(self):
        """Setup logging for the parser."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def find_operating_manuals(self) -> Dict[str, List[Path]]:
        """Find all operating manual PDFs in the Machines directory."""
        manuals = {}
        
        if not self.machines_dir.exists():
            self.logger.error(f"Machines directory not found: {self.machines_dir}")
            return manuals
        
        for machine_dir in self.machines_dir.iterdir():
            if machine_dir.is_dir():
                machine_name = machine_dir.name
                machine_manuals = []
                
                # Look for operating manuals in operatingManuals subdirectory
                operating_dir = machine_dir / "operatingManuals"
                if operating_dir.exists():
                    for pdf_file in operating_dir.glob("*.pdf"):
                        machine_manuals.append(pdf_file)
                
                # Also check root directory for any PDFs
                for pdf_file in machine_dir.glob("*.pdf"):
                    if "operating" in pdf_file.name.lower() or "manual" in pdf_file.name.lower():
                        machine_manuals.append(pdf_file)
                
                if machine_manuals:
                    manuals[machine_name] = machine_manuals
        
        return manuals
    
    def extract_pdf_text_by_page(self, pdf_path: Path) -> Dict[int, str]:
        """Extract text from PDF, returning dict of page_number -> text."""
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
    
    def find_table_of_contents(self, pages: Dict[int, str]) -> Optional[Tuple[int, str]]:
        """Find the table of contents page(s)."""
        toc_patterns = [
            r'(?i)table\s+of\s+contents',
            r'(?i)^contents\s*$',
            r'(?i)index'
        ]
        
        for page_num, text in pages.items():
            # Check first 10 pages typically
            if page_num > 10:
                break
                
            text_lines = text.split('\n')
            for line in text_lines[:20]:  # Check first 20 lines
                for pattern in toc_patterns:
                    if re.search(pattern, line.strip()):
                        self.logger.info(f"Found TOC pattern on page {page_num}: {line.strip()}")
                        return page_num, text
        
        return None
    
    def parse_toc_sections(self, toc_text: str) -> List[Dict[str, any]]:
        """Parse table of contents to extract sections and page numbers."""
        sections = []
        lines = toc_text.split('\n')
        
        # Patterns for TOC entries
        toc_patterns = [
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][^.]+?)\.?\s*\.+\s*(\d+)',  # "1.1 Safety .... 5"
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][^.]+?)\s+(\d+)\s*$',       # "1.1 Safety 5"
            r'^\s*(\d+)\.\s*([A-Z][^.]+?)\s*\.+\s*(\d+)',            # "1. Safety .... 5"
            r'^\s*([A-Z][A-Z\s]+?)\s*\.+\s*(\d+)',                   # "SAFETY .... 5"
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in toc_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        section_num, section_name, page_num = groups
                        sections.append({
                            'section_number': section_num.strip(),
                            'section_name': section_name.strip(),
                            'start_page': int(page_num),
                            'raw_line': line
                        })
                    elif len(groups) == 2:
                        section_name, page_num = groups
                        sections.append({
                            'section_number': '',
                            'section_name': section_name.strip(),
                            'start_page': int(page_num),
                            'raw_line': line
                        })
                    break
        
        return sections
    
    def find_sections_in_content(self, pages: Dict[int, str]) -> List[Dict[str, any]]:
        """Find section headers directly in content (fallback method)."""
        sections = []
        
        # Section header patterns
        header_patterns = [
            r'^\s*(\d+\.?\d*\.?)\s+([A-Z][A-Z\s]+)',        # "1.1 SAFETY PROCEDURES"
            r'^\s*([A-Z][A-Z\s]{3,})\s*$',                  # "SAFETY PROCEDURES"
            r'^\s*(\d+)\.\s*([A-Z][A-Z\s]+)',               # "1. SAFETY PROCEDURES"
        ]
        
        for page_num, text in pages.items():
            lines = text.split('\n')
            
            for line_idx, line in enumerate(lines):
                line = line.strip()
                
                for pattern in header_patterns:
                    match = re.match(pattern, line)
                    if match:
                        groups = match.groups()
                        if len(groups) == 2:
                            section_num, section_name = groups
                            sections.append({
                                'section_number': section_num.strip(),
                                'section_name': section_name.strip(),
                                'start_page': page_num,
                                'raw_line': line,
                                'method': 'content_scan'
                            })
                        elif len(groups) == 1:
                            section_name = groups[0]
                            sections.append({
                                'section_number': '',
                                'section_name': section_name.strip(),
                                'start_page': page_num,
                                'raw_line': line,
                                'method': 'content_scan'
                            })
        
        return sections
    
    def test_manual_parsing(self, pdf_path: Path) -> Dict[str, any]:
        """Test section parsing on a single manual."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Testing: {pdf_path.name}")
        self.logger.info(f"Path: {pdf_path}")
        
        result = {
            'file': pdf_path.name,
            'path': str(pdf_path),
            'success': False,
            'pages_extracted': 0,
            'toc_found': False,
            'toc_page': None,
            'sections_from_toc': [],
            'sections_from_content': [],
            'error': None
        }
        
        try:
            # Extract all pages
            pages = self.extract_pdf_text_by_page(pdf_path)
            result['pages_extracted'] = len(pages)
            
            if not pages:
                result['error'] = "No text extracted from PDF"
                return result
            
            self.logger.info(f"✅ Extracted text from {len(pages)} pages")
            
            # Try to find table of contents
            toc_result = self.find_table_of_contents(pages)
            if toc_result:
                toc_page, toc_text = toc_result
                result['toc_found'] = True
                result['toc_page'] = toc_page
                
                # Parse TOC sections
                toc_sections = self.parse_toc_sections(toc_text)
                result['sections_from_toc'] = toc_sections
                
                self.logger.info(f"✅ Found TOC on page {toc_page}")
                self.logger.info(f"✅ Extracted {len(toc_sections)} sections from TOC")
                
                for section in toc_sections[:5]:  # Show first 5
                    self.logger.info(f"  📖 {section['section_name']} (page {section['start_page']})")
            else:
                self.logger.warning("⚠️ No table of contents found")
            
            # Try content scanning as fallback
            content_sections = self.find_sections_in_content(pages)
            result['sections_from_content'] = content_sections
            
            if content_sections:
                self.logger.info(f"✅ Found {len(content_sections)} sections via content scan")
                for section in content_sections[:5]:  # Show first 5
                    self.logger.info(f"  📄 {section['section_name']} (page {section['start_page']})")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Error parsing {pdf_path.name}: {e}")
        
        return result
    
    def run_prototype_tests(self) -> Dict[str, any]:
        """Run the complete prototype test suite."""
        self.logger.info("🚀 Starting PDF Section Parser Prototype Tests")
        
        # Find all manuals
        manuals = self.find_operating_manuals()
        
        if not manuals:
            self.logger.error("❌ No operating manuals found")
            return {'error': 'No manuals found'}
        
        self.logger.info(f"📚 Found manuals for {len(manuals)} machines")
        for machine, manual_list in manuals.items():
            self.logger.info(f"  🔧 {machine}: {len(manual_list)} manual(s)")
        
        # Test parsing on a sample
        test_results = []
        
        # Test first manual from each machine (or specific ones)
        test_count = 0
        max_tests = 5  # Limit for prototype
        
        for machine_name, manual_list in manuals.items():
            if test_count >= max_tests:
                break
                
            # Test first manual for each machine
            manual_path = manual_list[0]
            result = self.test_manual_parsing(manual_path)
            result['machine'] = machine_name
            test_results.append(result)
            test_count += 1
        
        # Summary
        successful = sum(1 for r in test_results if r['success'])
        with_toc = sum(1 for r in test_results if r['toc_found'])
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("📊 PROTOTYPE TEST SUMMARY")
        self.logger.info(f"✅ Successfully parsed: {successful}/{len(test_results)} manuals")
        self.logger.info(f"📖 Found TOC in: {with_toc}/{len(test_results)} manuals")
        
        return {
            'total_machines': len(manuals),
            'total_manuals': sum(len(manual_list) for manual_list in manuals.values()),
            'tested_manuals': len(test_results),
            'successful_parses': successful,
            'toc_found_count': with_toc,
            'test_results': test_results
        }


def main():
    """Run the prototype tests."""
    parser = SectionParser()
    results = parser.run_prototype_tests()
    
    if 'error' in results:
        print(f"❌ {results['error']}")
        return 1
    
    print(f"\n🎯 Prototype Results:")
    print(f"   Machines found: {results['total_machines']}")
    print(f"   Total manuals: {results['total_manuals']}")
    print(f"   Tested: {results['tested_manuals']}")
    print(f"   Success rate: {results['successful_parses']}/{results['tested_manuals']}")
    print(f"   TOC detection: {results['toc_found_count']}/{results['tested_manuals']}")
    
    if results['successful_parses'] > 0:
        print("\n✅ Section parsing looks promising! Ready to proceed with full implementation.")
    else:
        print("\n⚠️ Section parsing needs refinement before proceeding.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())