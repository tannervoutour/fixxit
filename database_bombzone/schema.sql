-- Machine Documentation Database Schema
-- This database stores and indexes machine documentation for AI-powered search
-- Created: 2025-05-27

-- Core machines table - defines the equipment hierarchy
CREATE TABLE IF NOT EXISTS machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_name TEXT NOT NULL UNIQUE,           -- e.g., 'CSP', 'Feeder_1', 'PowerPress'
    machine_type TEXT,                           -- e.g., 'separator', 'feeder', 'press', 'dryer'
    line_number TEXT,                            -- e.g., 'Line_1', 'Line_2', 'General'
    location TEXT,                               -- Physical location or area
    manufacturer TEXT,                           -- Equipment manufacturer
    model TEXT,                                  -- Specific model number
    description TEXT,                            -- Brief description of function
    directory_path TEXT,                         -- Relative path to machine's document folder
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document registry - tracks all files and their metadata
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER,                          -- Links to machines table
    file_path TEXT NOT NULL,                     -- Relative path to the file
    filename TEXT NOT NULL,                      -- Original filename
    document_type TEXT NOT NULL,                 -- 'manual', 'diagram', 'parts', 'context', 'general', 'info'
    file_extension TEXT,                         -- '.pdf', '.txt', etc.
    title TEXT,                                  -- Document title (extracted or inferred)
    content_hash TEXT,                           -- SHA-256 hash of file content
    file_size INTEGER,                           -- File size in bytes
    page_count INTEGER DEFAULT 1,               -- Number of pages (1 for text files)
    language TEXT DEFAULT 'en',                 -- Document language
    is_processed BOOLEAN DEFAULT FALSE,         -- Whether content has been extracted
    processing_status TEXT DEFAULT 'pending',   -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

-- Document pages - stores page-level content and metadata
CREATE TABLE IF NOT EXISTS document_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,               -- Page number within document (1-based)
    content_text TEXT,                          -- Extracted raw text content
    content_cleaned TEXT,                       -- Cleaned and normalized text
    content_summary TEXT,                       -- AI-generated summary of page content
    section_title TEXT,                         -- Section or chapter title if identifiable
    keywords TEXT,                              -- Comma-separated extracted keywords
    word_count INTEGER DEFAULT 0,              -- Number of words on page
    has_images BOOLEAN DEFAULT FALSE,           -- Whether page contains diagrams/images
    has_tables BOOLEAN DEFAULT FALSE,           -- Whether page contains tables
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, page_number)
);

-- Content chunks - smaller searchable segments for semantic search
CREATE TABLE IF NOT EXISTS content_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    page_number INTEGER,                        -- Source page number
    chunk_index INTEGER NOT NULL,              -- Chunk number within document (0-based)
    chunk_text TEXT NOT NULL,                  -- The actual text chunk (500-1000 words)
    chunk_summary TEXT,                        -- Brief summary of chunk content
    chunk_type TEXT DEFAULT 'content',         -- 'content', 'procedure', 'specification', 'troubleshooting'
    keywords TEXT,                              -- Comma-separated keywords for this chunk
    word_count INTEGER DEFAULT 0,              -- Number of words in chunk
    start_char INTEGER,                         -- Character position where chunk starts in full text
    end_char INTEGER,                           -- Character position where chunk ends
    embedding_vector BLOB,                      -- Serialized embedding vector for semantic search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Search keywords - normalized keywords for fast text search
CREATE TABLE IF NOT EXISTS search_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,                      -- Normalized keyword
    keyword_type TEXT,                          -- 'machine', 'part', 'procedure', 'error', 'general'
    frequency INTEGER DEFAULT 1,               -- How often this keyword appears
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword)
);

-- Document keyword relationships - many-to-many linking
CREATE TABLE IF NOT EXISTS document_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    page_numbers TEXT,                          -- Comma-separated list of pages containing keyword
    frequency INTEGER DEFAULT 1,               -- Frequency of keyword in this document
    relevance_score REAL DEFAULT 0.5,          -- Computed relevance (0.0 to 1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES search_keywords(id) ON DELETE CASCADE,
    UNIQUE(document_id, keyword_id)
);

-- Machine relationships - defines how machines are connected
CREATE TABLE IF NOT EXISTS machine_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_machine_id INTEGER,                  -- Parent machine (e.g., Line_1)
    child_machine_id INTEGER,                   -- Child machine (e.g., Feeder_1)
    relationship_type TEXT,                     -- 'contains', 'feeds_into', 'controls', 'shares_docs'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_machine_id) REFERENCES machines(id) ON DELETE CASCADE,
    FOREIGN KEY (child_machine_id) REFERENCES machines(id) ON DELETE CASCADE,
    UNIQUE(parent_machine_id, child_machine_id, relationship_type)
);

-- Search history and analytics
CREATE TABLE IF NOT EXISTS search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,                  -- Original search query
    query_type TEXT,                           -- 'keyword', 'semantic', 'hybrid'
    machine_filter TEXT,                       -- Machine name filter applied
    document_type_filter TEXT,                 -- Document type filter applied
    results_count INTEGER DEFAULT 0,           -- Number of results returned
    execution_time_ms INTEGER,                 -- Query execution time in milliseconds
    user_id TEXT,                              -- User identifier (optional)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processing logs for monitoring and debugging
CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    operation TEXT NOT NULL,                   -- 'extract', 'chunk', 'embed', 'index'
    status TEXT NOT NULL,                      -- 'started', 'completed', 'failed'
    message TEXT,                              -- Status message or error details
    processing_time_ms INTEGER,               -- Time taken for operation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_documents_machine_id ON documents(machine_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(is_processed);
CREATE INDEX IF NOT EXISTS idx_document_pages_document_id ON document_pages(document_id);
CREATE INDEX IF NOT EXISTS idx_content_chunks_document_id ON content_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_content_chunks_type ON content_chunks(chunk_type);
CREATE INDEX IF NOT EXISTS idx_search_keywords_keyword ON search_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_document_keywords_document_id ON document_keywords(document_id);
CREATE INDEX IF NOT EXISTS idx_document_keywords_keyword_id ON document_keywords(keyword_id);
CREATE INDEX IF NOT EXISTS idx_machine_relationships_parent ON machine_relationships(parent_machine_id);
CREATE INDEX IF NOT EXISTS idx_machine_relationships_child ON machine_relationships(child_machine_id);

-- Full-text search indexes for SQLite FTS5
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    content,
    keywords,
    content='',  -- External content table
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    content_text,
    content_summary,
    section_title,
    keywords,
    content='',  -- External content table
    content_rowid='id'
);

-- Views for common queries
CREATE VIEW IF NOT EXISTS machine_document_summary AS
SELECT 
    m.machine_name,
    m.machine_type,
    m.line_number,
    COUNT(d.id) as total_documents,
    COUNT(CASE WHEN d.document_type = 'manual' THEN 1 END) as manual_count,
    COUNT(CASE WHEN d.document_type = 'diagram' THEN 1 END) as diagram_count,
    COUNT(CASE WHEN d.document_type = 'parts' THEN 1 END) as parts_count,
    COUNT(CASE WHEN d.document_type = 'context' THEN 1 END) as context_count,
    COUNT(CASE WHEN d.is_processed = 1 THEN 1 END) as processed_count,
    SUM(d.page_count) as total_pages
FROM machines m
LEFT JOIN documents d ON m.id = d.machine_id
GROUP BY m.id, m.machine_name;

CREATE VIEW IF NOT EXISTS document_processing_status AS
SELECT 
    d.filename,
    d.document_type,
    m.machine_name,
    d.processing_status,
    d.page_count,
    COUNT(dp.id) as processed_pages,
    COUNT(cc.id) as content_chunks,
    d.created_at,
    d.updated_at
FROM documents d
JOIN machines m ON d.machine_id = m.id
LEFT JOIN document_pages dp ON d.id = dp.document_id
LEFT JOIN content_chunks cc ON d.id = cc.document_id
GROUP BY d.id;

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

CREATE TRIGGER IF NOT EXISTS update_page_timestamp
    AFTER UPDATE ON document_pages
BEGIN
    UPDATE document_pages SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;