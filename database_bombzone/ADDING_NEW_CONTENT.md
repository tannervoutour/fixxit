# Adding New Content to Machine Documentation Database

## 📋 Quick Reference Guide

This guide explains how to add new machines, documents, and content to the AI-powered documentation search system.

## 🚀 Quick Steps for Adding Content

### 1. Add New Machine
```bash
# Create machine directory
mkdir -p Machines/NewMachineName

# Create subdirectories
cd Machines/NewMachineName
mkdir -p operatingManuals spareParts Diagrams info subComponents

# Add description file
echo "Machine description here" > NewMachineName-generalDescription.txt
```

### 2. Add Documents
```bash
# Copy files to appropriate directories
cp operating_manual.pdf operatingManuals/
cp spare_parts_list.pdf spareParts/
cp wiring_diagram.pdf Diagrams/
```

### 3. Process New Content
```bash
# Run database update
python setup_database.py

# Or process specific machine
python -c "
from document_processor import DocumentProcessor
processor = DocumentProcessor('machine_docs.db', '.')
processor._process_machine_directory(Path('Machines/NewMachineName'))
"
```

## 📂 Directory Structure Template

### Complete Machine Directory Structure
```
Machines/
└── {MachineName}/
    ├── {MachineName}-generalDescription.txt     # Required: Basic description
    ├── Pinned Context — {Description}.txt       # Recommended: Key info
    ├── operatingManuals/                         # Operating procedures
    │   ├── {MachineName}_operating.pdf
    │   ├── {MachineName}_installation.pdf
    │   └── error_codes_manual.pdf
    ├── spareParts/                               # Parts and maintenance
    │   ├── {MachineName}_spare_parts.pdf
    │   └── maintenance_schedule.pdf
    ├── Diagrams/                                 # Technical diagrams
    │   ├── {MachineName}_wiring.pdf
    │   ├── {MachineName}_pneumatic.pdf
    │   └── {MachineName}_hydraulic.pdf
    ├── info/                                     # Additional information
    │   ├── specifications.txt
    │   └── technical_notes.pdf
    └── subComponents/                            # Component-specific docs
        ├── motor_manual.pdf
        └── control_panel_guide.pdf
```

## 📝 File Naming Conventions

### Recommended Naming Patterns
- **Operating Manuals**: `{MachineName}_operating.pdf`, `{MachineName}_manual.pdf`
- **Spare Parts**: `{MachineName}_spare_parts.pdf`, `parts_list.pdf`
- **Diagrams**: `{MachineName}_wiring.pdf`, `{MachineName}_pneumatic.pdf`
- **General Info**: `{MachineName}-generalDescription.txt`
- **Context Files**: `Pinned Context — {Description}.txt`

### File Type Guidelines
- **PDF Files**: Best for manuals, parts lists, detailed procedures
- **Text Files**: Best for quick reference, descriptions, context
- **Avoid**: Image-only PDFs (text cannot be extracted)

## 📋 Document Type Classification

The system automatically classifies documents based on their location:

| Directory | Document Type | Purpose |
|-----------|---------------|---------|
| `operatingManuals/` | manual | Operating procedures, troubleshooting |
| `spareParts/` | parts | Parts lists, maintenance schedules |
| `Diagrams/` | diagram | Wiring, pneumatic, hydraulic diagrams |
| `info/` | info | Additional technical information |
| `subComponents/` | component | Component-specific documentation |
| Root with `generalDescription.txt` | general | Basic machine overview |
| `Pinned Context` files | context | Key operational information |

## 🏭 Machine Information Templates

### General Description Template
Create `{MachineName}-generalDescription.txt`:
```
Pinned Context — {Machine Name} "{Short Code}" ({Type})
Use this text whenever a question mentions "{machine names}", "{aliases}", or {context}.

Quick-ID
• Type: {Manufacturer} {Model} {Function}
• Task: {Primary purpose and function}
• Key modules: {Main components}
• Normal set-points: {Operating parameters}
• Operating modes: {Available modes}

What the {Machine} Does (operator view)
1. {Step 1} – {Description}
2. {Step 2} – {Description}
3. {Step 3} – {Description}
4. {Step 4} – {Description}

Useful Front-Panel Touches
• {Control 1} – {Function}
• {Control 2} – {Function}
• {Control 3} – {Function}

Why It Matters
• {Benefit 1} – {Description}
• {Benefit 2} – {Description}
• {Benefit 3} – {Description}

Quick Glossary
• {Term 1} – {Definition}
• {Term 2} – {Definition}
• {Term 3} – {Definition}

60-Second Summary
{Comprehensive summary of machine purpose, operation, and importance}
```

### Pinned Context Template
Create `Pinned Context — {Description}.txt`:
```
Pinned Context — {Specific Context} "{Code/ID}"
Use this text whenever a question mentions {trigger keywords}.

Quick-ID
• Type: {Specific identification}
• Task: {Specific function}
• Key Information: {Critical details}

{Structured content relevant to this specific context}
```

## 🔄 Processing Workflow

### Automatic Processing
When you run `python setup_database.py`, the system:

1. **Scans** all machine directories
2. **Identifies** new or modified files
3. **Extracts** text content from PDFs and text files
4. **Creates** searchable chunks for AI processing
5. **Indexes** keywords and generates embeddings
6. **Updates** the searchable database

### Manual Processing Steps

#### For Individual Machines
```python
from document_processor import DocumentProcessor
from pathlib import Path

processor = DocumentProcessor("machine_docs.db", ".")

# Process specific machine
machine_dir = Path("Machines/YourMachineName")
results = processor._process_machine_directory(machine_dir)
print(f"Processed {results['documents_processed']} documents")
```

#### For Individual Documents
```python
# Process single document
document_path = Path("Machines/YourMachine/operatingManuals/new_manual.pdf")
machine_id = 1  # Get from database
results = processor._process_document(document_path, machine_id, "manual")
```

### Verify Processing
```python
from search_engine import DocumentSearchEngine

search = DocumentSearchEngine("machine_docs.db")

# Test search for new content
results = search.search_documents("YourMachineName operating")
print(f"Found {len(results)} results for new machine")
```

## 🔍 Content Quality Guidelines

### For Better Search Results

#### Text Quality
- **Readable PDFs**: Ensure PDFs contain searchable text
- **Clear Language**: Use consistent terminology
- **Complete Information**: Include all relevant details
- **Structured Content**: Use headings and sections

#### Keywords and Context
- **Machine Names**: Include all aliases and nicknames
- **Part Numbers**: Include exact part numbers and variations
- **Procedures**: Use consistent procedure naming
- **Error Codes**: Include all error codes and descriptions

#### File Organization
- **Logical Grouping**: Group related documents together
- **Version Control**: Use clear version naming
- **Complete Sets**: Include all related documentation
- **Regular Updates**: Keep documentation current

## 🛠️ Machine Relationships

### Defining Machine Relationships
For machines that are part of larger systems:

```python
import sqlite3

with sqlite3.connect("machine_docs.db") as conn:
    cursor = conn.cursor()
    
    # Define parent-child relationship
    cursor.execute("""
        INSERT INTO machine_relationships 
        (parent_machine_id, child_machine_id, relationship_type)
        VALUES (
            (SELECT id FROM machines WHERE machine_name = 'Line_1'),
            (SELECT id FROM machines WHERE machine_name = 'Feeder_1'),
            'contains'
        )
    """)
```

### Relationship Types
- **contains**: Parent contains child (Line_1 contains Feeder_1)
- **feeds_into**: Output goes to next machine
- **controls**: One machine controls another
- **shares_docs**: Machines share documentation

## 📊 Monitoring and Maintenance

### Check Processing Status
```python
from document_processor import DocumentProcessor

processor = DocumentProcessor("machine_docs.db")
status = processor.get_processing_status()

print(f"Total documents: {status['total_documents']}")
print(f"Processed: {status['processed_documents']}")
print(f"Failed: {status['failed_documents']}")
```

### Common Issues and Solutions

#### PDF Processing Issues
- **Problem**: "Text extraction failed"
- **Solution**: Ensure PDF contains searchable text, not just images
- **Fix**: Use OCR tools to convert image PDFs to text PDFs

#### Missing Search Results
- **Problem**: New documents don't appear in search
- **Solution**: Check processing status and re-run setup
- **Fix**: Verify file paths and document classification

#### Poor Search Relevance
- **Problem**: Irrelevant search results
- **Solution**: Improve document content and keywords
- **Fix**: Add pinned context files with key information

## 🔧 Advanced Configuration

### Custom Document Types
To add new document types, modify `document_processor.py`:

```python
self.document_type_mapping = {
    'operatingManuals': 'manual',
    'spareParts': 'parts',
    'Diagrams': 'diagram',
    'info': 'info',
    'newDocType': 'custom',  # Add new type
    # ... existing mappings
}
```

### Search Optimization
For better search performance:

1. **Regular Reindexing**: Run setup periodically
2. **Content Quality**: Improve document text quality
3. **Keyword Enhancement**: Add relevant keywords to content
4. **Context Files**: Create comprehensive context files

### Database Maintenance
```python
# Clean up old processing logs
with sqlite3.connect("machine_docs.db") as conn:
    conn.execute("""
        DELETE FROM processing_logs 
        WHERE created_at < datetime('now', '-30 days')
    """)
```

## 🚀 Best Practices Summary

### Do's ✅
- **Consistent Naming**: Use clear, consistent file names
- **Complete Documentation**: Include all available documents
- **Regular Updates**: Keep content current and accurate
- **Quality Content**: Ensure PDFs have searchable text
- **Context Files**: Create pinned context for key information
- **Test Searches**: Verify new content appears in search results

### Don'ts ❌
- **Image-Only PDFs**: Avoid PDFs that are just scanned images
- **Inconsistent Naming**: Don't use random or unclear file names
- **Missing Descriptions**: Don't skip general description files
- **Incomplete Processing**: Don't forget to run setup after adding files
- **Poor Organization**: Don't place files in wrong directories

## 📞 Support and Troubleshooting

### Getting Help
1. **Check Logs**: Review processing logs for errors
2. **Test Basic Functions**: Run `simple_test.py`
3. **Verify Structure**: Ensure correct directory structure
4. **Check Processing**: Verify all documents processed successfully

### Common Commands
```bash
# Full system setup
python setup_database.py

# Basic functionality test
python simple_test.py

# Check database status
python -c "
from document_processor import DocumentProcessor
p = DocumentProcessor('machine_docs.db')
print(p.get_processing_status())
"

# Test search
python -c "
from search_engine import DocumentSearchEngine
s = DocumentSearchEngine('machine_docs.db')
results = s.search_documents('your search query')
print(f'Found {len(results)} results')
"
```

This system provides a robust foundation for managing and searching machine documentation with AI-powered capabilities. Follow these guidelines to ensure optimal performance and search quality.