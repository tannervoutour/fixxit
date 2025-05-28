-- Machine Documentation Database Schema
-- This database stores machine documentation with section-level granularity
-- Created: 2025-05-27

-- Machines table - defines the equipment hierarchy
CREATE TABLE IF NOT EXISTS machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_name TEXT NOT NULL UNIQUE,           -- e.g., 'CSP', 'Feeder', 'Folder', 'Ironer'
    machine_type TEXT,                           -- e.g., 'separator', 'feeder', 'folder', 'ironer'
    line_number TEXT,                            -- e.g., 'Line_1', 'Line_2', 'General'
    sub_machine TEXT,                            -- For Line machines: 'Feeder', 'Folder', 'Ironer'
    location TEXT,                               -- Physical location or area
    description TEXT,                            -- Brief description of function
    directory_path TEXT,                         -- Relative path to machine's document folder
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table - tracks manual files
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL,                 -- Links to machines table
    file_path TEXT NOT NULL,                     -- Relative path to the file
    filename TEXT NOT NULL,                      -- Original filename
    document_type TEXT NOT NULL DEFAULT 'manual', -- 'manual', 'diagram', 'parts' (focusing on manuals for now)
    file_extension TEXT,                         -- '.pdf', '.txt'
    title TEXT,                                  -- Document title (extracted or inferred)
    content_hash TEXT,                           -- SHA-256 hash of file content
    file_size INTEGER,                           -- File size in bytes
    page_count INTEGER DEFAULT 1,               -- Number of pages
    is_processed BOOLEAN DEFAULT FALSE,         -- Whether sections have been extracted
    processing_status TEXT DEFAULT 'pending',   -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

-- Document sections - the core table for AI queries
CREATE TABLE IF NOT EXISTS document_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    machine_id INTEGER NOT NULL,                -- Denormalized for faster queries
    section_name TEXT NOT NULL,                 -- e.g., 'Safety', 'Operation', 'Troubleshooting'
    section_title TEXT,                         -- Full section title from document
    start_page INTEGER NOT NULL,               -- First page of this section
    end_page INTEGER,                           -- Last page of this section (nullable)
    content_text TEXT NOT NULL,                -- Full text content of the section
    content_summary TEXT,                       -- AI-generated summary (future)
    keywords TEXT,                              -- Comma-separated keywords for search
    word_count INTEGER DEFAULT 0,              -- Number of words in section
    section_order INTEGER DEFAULT 0,           -- Order of section in document
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

-- Search keywords - normalized keywords for fast text search
CREATE TABLE IF NOT EXISTS search_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,                      -- Normalized keyword
    keyword_type TEXT,                          -- 'machine', 'procedure', 'safety', 'troubleshooting'
    frequency INTEGER DEFAULT 1,               -- How often this keyword appears
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword)
);

-- Section keyword relationships - many-to-many linking
CREATE TABLE IF NOT EXISTS section_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    frequency INTEGER DEFAULT 1,               -- Frequency of keyword in this section
    relevance_score REAL DEFAULT 0.5,          -- Computed relevance (0.0 to 1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES document_sections(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES search_keywords(id) ON DELETE CASCADE,
    UNIQUE(section_id, keyword_id)
);

-- Processing logs for monitoring and debugging
CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    operation TEXT NOT NULL,                   -- 'extract', 'parse_sections', 'index'
    status TEXT NOT NULL,                      -- 'started', 'completed', 'failed'
    message TEXT,                              -- Status message or error details
    processing_time_ms INTEGER,               -- Time taken for operation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_machines_name ON machines(machine_name);
CREATE INDEX IF NOT EXISTS idx_machines_line ON machines(line_number);
CREATE INDEX IF NOT EXISTS idx_documents_machine_id ON documents(machine_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(is_processed);
CREATE INDEX IF NOT EXISTS idx_sections_document_id ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_sections_machine_id ON document_sections(machine_id);
CREATE INDEX IF NOT EXISTS idx_sections_name ON document_sections(section_name);
CREATE INDEX IF NOT EXISTS idx_search_keywords_keyword ON search_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_section_keywords_section_id ON section_keywords(section_id);

-- Full-text search indexes for SQLite FTS5
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
    section_name,
    section_title,
    content_text,
    keywords,
    content='document_sections',
    content_rowid='id'
);

-- Views for common queries
CREATE VIEW IF NOT EXISTS machine_documentation_summary AS
SELECT 
    m.machine_name,
    m.machine_type,
    m.line_number,
    m.sub_machine,
    COUNT(DISTINCT d.id) as total_documents,
    COUNT(DISTINCT ds.id) as total_sections,
    COUNT(CASE WHEN d.is_processed = 1 THEN 1 END) as processed_documents,
    SUM(d.page_count) as total_pages,
    GROUP_CONCAT(DISTINCT ds.section_name) as available_sections
FROM machines m
LEFT JOIN documents d ON m.id = d.machine_id
LEFT JOIN document_sections ds ON m.id = ds.machine_id
GROUP BY m.id, m.machine_name;

CREATE VIEW IF NOT EXISTS section_search_view AS
SELECT 
    ds.id,
    m.machine_name,
    m.line_number,
    m.sub_machine,
    d.filename,
    ds.section_name,
    ds.section_title,
    ds.start_page,
    ds.content_text,
    ds.keywords,
    ds.word_count
FROM document_sections ds
JOIN machines m ON ds.machine_id = m.id
JOIN documents d ON ds.document_id = d.id
WHERE d.is_processed = 1;

-- Triggers for maintaining data consistency
CREATE TRIGGER IF NOT EXISTS update_machine_timestamp
    AFTER UPDATE ON machines
BEGIN
    UPDATE machines SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_document_timestamp
    AFTER UPDATE ON documents
BEGIN
    UPDATE documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_section_timestamp
    AFTER UPDATE ON document_sections
BEGIN
    UPDATE document_sections SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to update FTS index when sections are added/updated
CREATE TRIGGER IF NOT EXISTS sections_fts_insert
    AFTER INSERT ON document_sections
BEGIN
    INSERT INTO sections_fts(rowid, section_name, section_title, content_text, keywords)
    VALUES (NEW.id, NEW.section_name, NEW.section_title, NEW.content_text, NEW.keywords);
END;

CREATE TRIGGER IF NOT EXISTS sections_fts_update
    AFTER UPDATE ON document_sections
BEGIN
    UPDATE sections_fts 
    SET section_name = NEW.section_name, 
        section_title = NEW.section_title,
        content_text = NEW.content_text,
        keywords = NEW.keywords
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS sections_fts_delete
    AFTER DELETE ON document_sections
BEGIN
    DELETE FROM sections_fts WHERE rowid = OLD.id;
END;