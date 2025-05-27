#!/usr/bin/env python3
"""
Database Setup and Initialization Script
Sets up the machine documentation database and processes initial documents.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from document_processor import DocumentProcessor
from search_engine import DocumentSearchEngine


def setup_logging():
    """Configure logging for setup process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('setup.log')
        ]
    )
    return logging.getLogger('DatabaseSetup')


def check_dependencies():
    """Check if required dependencies are available."""
    logger = logging.getLogger('DatabaseSetup')
    missing_deps = []
    
    try:
        import PyPDF2
        logger.info("✅ PyPDF2 available for PDF processing")
    except ImportError:
        missing_deps.append("PyPDF2")
        logger.warning("⚠️ PyPDF2 not available - PDF processing will be limited")
    
    try:
        import nltk
        logger.info("✅ NLTK available for text processing")
    except ImportError:
        missing_deps.append("nltk")
        logger.warning("⚠️ NLTK not available - keyword extraction will be basic")
    
    try:
        import sentence_transformers
        logger.info("✅ SentenceTransformers available for semantic search")
    except ImportError:
        missing_deps.append("sentence-transformers")
        logger.warning("⚠️ SentenceTransformers not available - no semantic search")
    
    try:
        import sklearn
        logger.info("✅ Scikit-learn available for similarity calculations")
    except ImportError:
        missing_deps.append("scikit-learn")
        logger.warning("⚠️ Scikit-learn not available - similarity calculations limited")
    
    if missing_deps:
        logger.warning(f"⚠️ Missing dependencies: {', '.join(missing_deps)}")
        logger.info("Install with: pip install " + " ".join(missing_deps))
    
    return len(missing_deps) == 0


def initialize_database(database_path: str, base_directory: str):
    """Initialize the database and process documents."""
    logger = logging.getLogger('DatabaseSetup')
    
    logger.info("🚀 Starting database initialization...")
    
    # Initialize processor
    processor = DocumentProcessor(
        database_path=database_path,
        base_directory=base_directory
    )
    
    # Process all documents
    logger.info("📂 Scanning and processing documents...")
    results = processor.scan_and_index_all()
    
    # Log results
    logger.info("📊 Processing Results:")
    logger.info(f"   Machines processed: {results['machines_processed']}")
    logger.info(f"   Documents found: {results['documents_found']}")
    logger.info(f"   Documents processed: {results['documents_processed']}")
    logger.info(f"   Pages extracted: {results['pages_extracted']}")
    logger.info(f"   Content chunks created: {results['chunks_created']}")
    
    if results['errors']:
        logger.warning(f"⚠️ {len(results['errors'])} errors occurred:")
        for error in results['errors'][:5]:  # Show first 5 errors
            logger.warning(f"   - {error}")
        if len(results['errors']) > 5:
            logger.warning(f"   ... and {len(results['errors']) - 5} more errors")
    
    # Get final status
    status = processor.get_processing_status()
    logger.info("📈 Final Database Status:")
    logger.info(f"   Total documents: {status['total_documents']}")
    logger.info(f"   Processed documents: {status['processed_documents']}")
    logger.info(f"   Failed documents: {status['failed_documents']}")
    logger.info(f"   Total pages: {status['total_pages']}")
    
    return results, status


def test_search_functionality(database_path: str):
    """Test the search functionality with sample queries."""
    logger = logging.getLogger('DatabaseSetup')
    
    logger.info("🔍 Testing search functionality...")
    
    search_engine = DocumentSearchEngine(database_path)
    
    test_queries = [
        ("CSP separator", "Test basic machine search"),
        ("operating manual", "Test document type search"),
        ("troubleshooting", "Test troubleshooting search"),
        ("parts list", "Test parts documentation search")
    ]
    
    for query, description in test_queries:
        logger.info(f"   Testing: {description} - '{query}'")
        
        try:
            results = search_engine.search_documents(query, max_results=3)
            logger.info(f"     ✅ Found {len(results)} results")
            
            for i, result in enumerate(results[:2], 1):
                machine = result.get('machine_name', 'Unknown')
                filename = result.get('filename', 'Unknown')
                score = result.get('relevance_score', 0)
                logger.info(f"       {i}. {machine}/{filename} (score: {score:.3f})")
                
        except Exception as e:
            logger.error(f"     ❌ Search failed: {e}")
    
    logger.info("✅ Search testing complete")


def create_sample_queries_file(base_directory: str):
    """Create a file with sample queries for testing."""
    sample_queries = """# Sample Queries for Machine Documentation Search

## Basic Machine Information
- "CSP separator operating manual"
- "Feeder 1 troubleshooting guide"
- "PowerPress maintenance procedures"
- "Dryer parts list"

## Troubleshooting Queries
- "CSP separator not starting"
- "Feeder belt misalignment"
- "Press hydraulic problems"
- "Dryer temperature issues"

## Specific Component Searches
- "OP-35 control panel"
- "X6 touch screen manual"
- "hydraulic cylinder specifications"
- "motor wiring diagrams"

## Cross-Reference Searches
- "Line 1 complete documentation"
- "Ironer spare parts and manual"
- "Conveyor system overview"
- "Emergency stop procedures"

## Error Code Searches
- "error code E001"
- "fault code troubleshooting"
- "alarm reset procedures"
- "diagnostic messages"

## Maintenance Searches
- "preventive maintenance schedule"
- "lubrication points"
- "filter replacement"
- "calibration procedures"
"""
    
    with open(Path(base_directory) / "sample_queries.md", 'w') as f:
        f.write(sample_queries)


def main():
    """Main setup function."""
    logger = setup_logging()
    
    logger.info("🏭 Machine Documentation Database Setup")
    logger.info("=" * 50)
    
    # Configuration
    base_directory = Path(__file__).parent
    database_path = base_directory / "machine_docs.db"
    
    logger.info(f"📁 Base directory: {base_directory}")
    logger.info(f"🗄️ Database path: {database_path}")
    
    # Check dependencies
    logger.info("🔍 Checking dependencies...")
    all_deps_available = check_dependencies()
    
    if not all_deps_available:
        logger.warning("⚠️ Some dependencies are missing. Install them for full functionality.")
        logger.info("Run: pip install -r requirements.txt")
    
    # Check if Machines directory exists
    machines_dir = base_directory / "Machines"
    if not machines_dir.exists():
        logger.error(f"❌ Machines directory not found: {machines_dir}")
        logger.error("Please ensure the Machines directory with documentation exists.")
        return False
    
    logger.info(f"📂 Found Machines directory with {len(list(machines_dir.iterdir()))} items")
    
    # Initialize database
    try:
        results, status = initialize_database(str(database_path), str(base_directory))
        
        if results['documents_processed'] == 0:
            logger.warning("⚠️ No documents were processed successfully")
            return False
        
        # Test search functionality
        test_search_functionality(str(database_path))
        
        # Create sample queries file
        create_sample_queries_file(str(base_directory))
        logger.info("📝 Created sample_queries.md with example searches")
        
        logger.info("✅ Database setup complete!")
        logger.info("🚀 Ready for AI-powered document search!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)