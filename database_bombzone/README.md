# Machine Documentation Database System

## 🏭 Overview

This system provides AI-powered search and retrieval capabilities for machine documentation. It processes PDFs, text files, and various document types to create a searchable knowledge base with semantic search capabilities.

## 📂 System Components

### Core Files
- `schema.sql` - Database schema with comprehensive indexing
- `document_processor.py` - Processes and indexes documents
- `search_engine.py` - Provides intelligent search capabilities
- `document_search_tools.py` - MCP-compatible tools for AI integration
- `setup_database.py` - Automated setup and initialization script

### Database Structure
- **machines** - Equipment hierarchy and metadata
- **documents** - File registry with processing status
- **document_pages** - Page-level content and summaries
- **content_chunks** - Semantic search segments
- **search_keywords** - Normalized keywords for fast search
- **machine_relationships** - Equipment interconnections

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python setup_database.py
```

### 3. Test Search Functionality
```python
from search_engine import DocumentSearchEngine

search = DocumentSearchEngine("machine_docs.db")
results = search.search_documents("CSP separator troubleshooting")
```

## 🔧 Available Tools

### 1. `search_machine_documents`
Search through all machine documentation with natural language queries.

**Parameters:**
- `query` (str): Natural language search query
- `machine_name` (str, optional): Filter by specific machine
- `document_type` (str, optional): Filter by document type
- `max_results` (int): Maximum results to return

**Example:**
```python
search_machine_documents(
    query="hydraulic pressure troubleshooting",
    machine_name="PowerPress",
    document_type="manual",
    max_results=5
)
```

### 2. `get_document_content`
Retrieve specific pages from a document.

**Parameters:**
- `document_id` (int): Document ID from search results
- `page_numbers` (str, optional): Comma-separated page numbers or 'all'

### 3. `get_machine_overview`
Get comprehensive machine information and available documentation.

**Parameters:**
- `machine_name` (str): Machine to get overview for
- `include_context` (bool): Include pinned context information
- `include_diagrams` (bool): Include diagram references

### 4. `search_troubleshooting_info`
Specialized search for troubleshooting and error resolution.

**Parameters:**
- `problem_description` (str): Description of the problem
- `machine_name` (str, optional): Specific machine
- `error_code` (str, optional): Specific error code

### 5. `cross_reference_machine_docs`
Find related information across multiple document types.

**Parameters:**
- `machine_name` (str): Target machine
- `topic` (str): Topic to search for
- `document_types` (str, optional): Comma-separated document types

### 6. `get_document_suggestions`
Get search suggestions based on partial input.

**Parameters:**
- `partial_query` (str): Partial search query

## 📊 Search Features

### Hybrid Search
Combines keyword and semantic search for optimal results:
- **Keyword Search**: Fast, exact matching
- **Semantic Search**: Understanding context and intent
- **Ranking**: Intelligent relevance scoring

### Document Types
- **manual** - Operating manuals and procedures
- **diagram** - Wiring, pneumatic, hydraulic diagrams
- **parts** - Spare parts lists and specifications
- **context** - Pinned context files with key information
- **general** - General descriptions and overviews
- **info** - Additional technical information

### Content Features
- **Page-level precision** - Exact page references in results
- **Content previews** - Snippet previews of relevant content
- **Cross-references** - Links between related documents
- **Machine hierarchy** - Understanding of equipment relationships

## 🔄 Adding New Content

### Automated Processing
The system automatically processes new documents when you run:
```bash
python setup_database.py
```

### Manual Document Addition

#### 1. Add Files to Directory Structure
Place new files in the appropriate machine directory:
```
Machines/
├── {MachineName}/
│   ├── operatingManuals/    # PDF manuals
│   ├── spareParts/         # Parts lists
│   ├── Diagrams/           # Technical diagrams
│   ├── info/               # Additional info
│   └── {MachineName}-generalDescription.txt
```

#### 2. Update Machine Information
Create or update machine description files:
- `{MachineName}-generalDescription.txt` - Basic machine information
- `Pinned Context — {Description}.txt` - Key operational context

#### 3. Process New Documents
```python
from document_processor import DocumentProcessor

processor = DocumentProcessor("machine_docs.db", "/path/to/database_bombzone")
results = processor.scan_and_index_all()
```

### Supported File Types
- **PDF Files**: Automatic text extraction and page indexing
- **Text Files**: Direct content processing
- **Future**: Support for Word docs, images with OCR

### Document Type Classification
Files are automatically classified based on their location and naming:
- `operatingManuals/` → 'manual'
- `spareParts/` → 'parts'
- `Diagrams/` → 'diagram'
- `info/` → 'info'
- `Pinned Context` files → 'context'
- `generalDescription.txt` → 'general'

## 🎯 Best Practices

### Organizing Documents
1. **Consistent Naming**: Use descriptive, consistent filenames
2. **Proper Categorization**: Place files in appropriate subdirectories
3. **Complete Information**: Include general descriptions for all machines
4. **Context Files**: Create pinned context for key operational info

### Search Optimization
1. **Natural Language**: Use descriptive queries instead of single keywords
2. **Machine Filtering**: Specify machine names when searching specific equipment
3. **Document Types**: Filter by document type for targeted searches
4. **Cross-Reference**: Use cross-reference search for comprehensive information

### Content Quality
1. **Clear Text**: Ensure PDFs have readable text (not just images)
2. **Structured Content**: Use consistent formatting in documents
3. **Keywords**: Include relevant keywords in content and filenames
4. **Updates**: Regularly update and maintain document accuracy

## 🔍 Query Examples

### Basic Searches
- "CSP separator operating procedures"
- "Feeder belt alignment troubleshooting"
- "PowerPress hydraulic system maintenance"
- "Dryer temperature control wiring"

### Advanced Searches
- "Line 1 emergency stop procedures across all documents"
- "X6 touch screen error codes and reset procedures"
- "Preventive maintenance schedules for all conveyors"
- "Spare parts compatibility between Feeder 1 and Feeder 2"

### Troubleshooting Searches
- "Machine won't start after E-stop reset"
- "Hydraulic pressure loss during operation"
- "Conveyor belt tracking problems"
- "Touch screen not responding to inputs"

## 📈 Performance Monitoring

### Database Statistics
```python
processor = DocumentProcessor("machine_docs.db")
status = processor.get_processing_status()
print(f"Documents processed: {status['processed_documents']}")
print(f"Total pages: {status['total_pages']}")
```

### Search Analytics
The system tracks search queries and performance in the `search_queries` table for optimization.

## 🔧 Maintenance

### Regular Tasks
1. **Reindex Documents**: Run setup when documents are added/modified
2. **Check Processing Status**: Monitor for failed document processing
3. **Update Dependencies**: Keep search libraries current
4. **Database Cleanup**: Periodically clean old processing logs

### Troubleshooting
- **PDF Processing Issues**: Check PyPDF2 compatibility
- **Search Performance**: Monitor embedding model performance
- **Database Size**: Monitor database growth and optimize indexes
- **Memory Usage**: Watch memory usage with large document sets

## 🔐 Security Considerations

- **Read-Only Access**: Search tools provide read-only access to documents
- **Path Validation**: File paths are validated to prevent directory traversal
- **SQL Injection**: All queries use parameterized statements
- **Content Filtering**: Sensitive information detection can be added

## 🚀 Future Enhancements

### Planned Features
- **Image OCR**: Extract text from diagram images
- **Multi-language Support**: Support for non-English documents
- **Document Versioning**: Track document versions and changes
- **Real-time Updates**: Monitor file system for automatic updates
- **Advanced Analytics**: Document usage and search analytics
- **Integration APIs**: REST API for external system integration

### AI Enhancements
- **Query Understanding**: Better natural language query processing
- **Auto-summarization**: Automatic document summarization
- **Smart Recommendations**: Suggest related documents
- **Anomaly Detection**: Identify missing or outdated documentation

This system provides a solid foundation for AI-powered machine documentation search with room for extensive customization and enhancement based on specific operational needs.