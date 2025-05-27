#!/usr/bin/env python3
"""
Machine Documentation Search Engine
Provides intelligent search capabilities across machine documentation.
"""

import sqlite3
import re
import json
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class DocumentSearchEngine:
    """AI-powered search engine for machine documentation."""
    
    def __init__(self, database_path: str = "machine_docs.db"):
        """
        Initialize the search engine.
        
        Args:
            database_path: Path to the SQLite database
        """
        self.database_path = database_path
        self.logger = self._setup_logging()
        
        # Initialize embedding model (same as used in processing)
        self.embedding_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("✅ Loaded sentence transformer model for search")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load embedding model: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the search engine."""
        logger = logging.getLogger('DocumentSearchEngine')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def search_documents(self, query: str, machine_filter: str = None, 
                        document_type_filter: str = None, max_results: int = 10,
                        search_type: str = "hybrid") -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.
        
        Args:
            query: Natural language search query
            machine_filter: Optional machine name filter
            document_type_filter: Optional document type filter
            max_results: Maximum number of results to return
            search_type: 'keyword', 'semantic', or 'hybrid'
            
        Returns:
            List of search results with relevance scores
        """
        self.logger.info(f"🔍 Searching: '{query}' (type: {search_type})")
        
        if search_type == "semantic" and self.embedding_model:
            return self._semantic_search(query, machine_filter, document_type_filter, max_results)
        elif search_type == "keyword":
            return self._keyword_search(query, machine_filter, document_type_filter, max_results)
        else:
            # Hybrid search (default)
            return self._hybrid_search(query, machine_filter, document_type_filter, max_results)
    
    def _keyword_search(self, query: str, machine_filter: str = None,
                       document_type_filter: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Perform keyword-based search."""
        # Clean and prepare query
        keywords = self._extract_query_keywords(query)
        
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build search conditions
            conditions = []
            params = []
            
            # Keyword matching
            if keywords:
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append("""
                        (dp.content_cleaned LIKE ? OR 
                         dp.keywords LIKE ? OR 
                         d.title LIKE ? OR
                         m.machine_name LIKE ?)
                    """)
                    keyword_pattern = f"%{keyword}%"
                    params.extend([keyword_pattern] * 4)
                
                conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # Machine filter
            if machine_filter:
                conditions.append("m.machine_name LIKE ?")
                params.append(f"%{machine_filter}%")
            
            # Document type filter
            if document_type_filter:
                conditions.append("d.document_type = ?")
                params.append(document_type_filter)
            
            # Only processed documents
            conditions.append("d.is_processed = 1")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query_sql = f"""
                SELECT DISTINCT
                    d.id as document_id,
                    d.filename,
                    d.document_type,
                    d.title,
                    m.machine_name,
                    m.machine_type,
                    dp.page_number,
                    dp.content_cleaned,
                    dp.content_summary,
                    dp.section_title,
                    d.file_path,
                    0.5 as relevance_score  -- Simple scoring for keyword search
                FROM documents d
                JOIN machines m ON d.machine_id = m.id
                LEFT JOIN document_pages dp ON d.id = dp.document_id
                WHERE {where_clause}
                ORDER BY 
                    CASE WHEN d.document_type = 'context' THEN 1 ELSE 2 END,
                    d.filename
                LIMIT ?
            """
            
            params.append(max_results)
            cursor.execute(query_sql, params)
            results = cursor.fetchall()
        
        return [dict(row) for row in results]
    
    def _semantic_search(self, query: str, machine_filter: str = None,
                        document_type_filter: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic (embedding-based) search."""
        if not self.embedding_model or not SKLEARN_AVAILABLE:
            self.logger.warning("⚠️ Semantic search not available, falling back to keyword search")
            return self._keyword_search(query, machine_filter, document_type_filter, max_results)
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build base query with filters
                conditions = ["cc.embedding_vector IS NOT NULL"]
                params = []
                
                if machine_filter:
                    conditions.append("m.machine_name LIKE ?")
                    params.append(f"%{machine_filter}%")
                
                if document_type_filter:
                    conditions.append("d.document_type = ?")
                    params.append(document_type_filter)
                
                conditions.append("d.is_processed = 1")
                where_clause = " AND ".join(conditions)
                
                # Get all chunks with embeddings
                cursor.execute(f"""
                    SELECT 
                        cc.id as chunk_id,
                        cc.document_id,
                        cc.page_number,
                        cc.chunk_text,
                        cc.chunk_summary,
                        cc.embedding_vector,
                        d.filename,
                        d.document_type,
                        d.title,
                        d.file_path,
                        m.machine_name,
                        m.machine_type
                    FROM content_chunks cc
                    JOIN documents d ON cc.document_id = d.id
                    JOIN machines m ON d.machine_id = m.id
                    WHERE {where_clause}
                """, params)
                
                chunks = cursor.fetchall()
            
            if not chunks:
                return []
            
            # Calculate similarities
            similarities = []
            for chunk in chunks:
                try:
                    chunk_embedding = pickle.loads(chunk['embedding_vector'])
                    similarity = cosine_similarity(
                        [query_embedding], [chunk_embedding]
                    )[0][0]
                    
                    similarities.append({
                        'chunk_id': chunk['chunk_id'],
                        'document_id': chunk['document_id'],
                        'page_number': chunk['page_number'],
                        'filename': chunk['filename'],
                        'document_type': chunk['document_type'],
                        'title': chunk['title'],
                        'file_path': chunk['file_path'],
                        'machine_name': chunk['machine_name'],
                        'machine_type': chunk['machine_type'],
                        'content_cleaned': chunk['chunk_text'],
                        'content_summary': chunk['chunk_summary'],
                        'relevance_score': float(similarity)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error processing chunk embedding: {e}")
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['relevance_score'], reverse=True)
            return similarities[:max_results]
            
        except Exception as e:
            self.logger.error(f"❌ Semantic search failed: {e}")
            return self._keyword_search(query, machine_filter, document_type_filter, max_results)
    
    def _hybrid_search(self, query: str, machine_filter: str = None,
                      document_type_filter: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Combine keyword and semantic search results."""
        # Get keyword results
        keyword_results = self._keyword_search(query, machine_filter, document_type_filter, max_results * 2)
        
        # Get semantic results if available
        semantic_results = []
        if self.embedding_model and SKLEARN_AVAILABLE:
            semantic_results = self._semantic_search(query, machine_filter, document_type_filter, max_results * 2)
        
        # Combine and score results
        combined_results = {}
        
        # Add keyword results with lower base score
        for result in keyword_results:
            key = (result['document_id'], result.get('page_number', 1))
            if key not in combined_results:
                result['relevance_score'] = 0.3  # Base score for keyword match
                combined_results[key] = result
        
        # Add semantic results with higher scores
        for result in semantic_results:
            key = (result['document_id'], result.get('page_number', 1))
            if key in combined_results:
                # Boost existing results
                combined_results[key]['relevance_score'] = max(
                    combined_results[key]['relevance_score'],
                    result['relevance_score'] * 0.7 + 0.3
                )
            else:
                combined_results[key] = result
        
        # Sort by combined relevance score
        final_results = list(combined_results.values())
        final_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return final_results[:max_results]
    
    def _extract_query_keywords(self, query: str) -> List[str]:
        """Extract keywords from search query."""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
        
        # Filter out common words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'what', 'where', 'when', 'why', 'how', 'which', 'who', 'whom'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]  # Limit to top 10 keywords
    
    def get_document_content(self, document_id: int, page_numbers: List[int] = None) -> Dict[str, Any]:
        """
        Retrieve specific content from a document.
        
        Args:
            document_id: Document ID to retrieve
            page_numbers: Specific pages to retrieve (None for all)
            
        Returns:
            Document content with metadata
        """
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get document metadata
            cursor.execute("""
                SELECT d.*, m.machine_name, m.machine_type
                FROM documents d
                JOIN machines m ON d.machine_id = m.id
                WHERE d.id = ?
            """, (document_id,))
            
            doc_info = cursor.fetchone()
            if not doc_info:
                return {"error": "Document not found"}
            
            # Get page content
            if page_numbers:
                placeholders = ','.join(['?'] * len(page_numbers))
                page_query = f"""
                    SELECT * FROM document_pages 
                    WHERE document_id = ? AND page_number IN ({placeholders})
                    ORDER BY page_number
                """
                params = [document_id] + page_numbers
            else:
                page_query = """
                    SELECT * FROM document_pages 
                    WHERE document_id = ? 
                    ORDER BY page_number
                """
                params = [document_id]
            
            cursor.execute(page_query, params)
            pages = cursor.fetchall()
        
        return {
            "document": dict(doc_info),
            "pages": [dict(page) for page in pages],
            "total_pages": len(pages)
        }
    
    def get_machine_overview(self, machine_name: str, include_context: bool = True,
                           include_diagrams: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive overview of a specific machine.
        
        Args:
            machine_name: Name of the machine
            include_context: Include pinned context information
            include_diagrams: Include diagram references
            
        Returns:
            Machine overview with relevant documents
        """
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get machine info
            cursor.execute("""
                SELECT * FROM machines WHERE machine_name LIKE ?
            """, (f"%{machine_name}%",))
            
            machine = cursor.fetchone()
            if not machine:
                return {"error": "Machine not found"}
            
            # Get document summary
            cursor.execute("""
                SELECT document_type, COUNT(*) as count, 
                       GROUP_CONCAT(filename) as files
                FROM documents 
                WHERE machine_id = ? AND is_processed = 1
                GROUP BY document_type
            """, (machine['id'],))
            
            doc_summary = cursor.fetchall()
            
            # Get context documents if requested
            context_docs = []
            if include_context:
                cursor.execute("""
                    SELECT d.*, dp.content_cleaned
                    FROM documents d
                    LEFT JOIN document_pages dp ON d.id = dp.document_id
                    WHERE d.machine_id = ? AND d.document_type = 'context'
                    ORDER BY d.filename
                """, (machine['id'],))
                context_docs = cursor.fetchall()
            
            # Get diagram references if requested  
            diagram_docs = []
            if include_diagrams:
                cursor.execute("""
                    SELECT filename, title, file_path
                    FROM documents
                    WHERE machine_id = ? AND document_type = 'diagram'
                    ORDER BY filename
                """, (machine['id'],))
                diagram_docs = cursor.fetchall()
        
        return {
            "machine": dict(machine),
            "document_summary": [dict(doc) for doc in doc_summary],
            "context_documents": [dict(doc) for doc in context_docs],
            "diagram_references": [dict(doc) for doc in diagram_docs]
        }
    
    def search_troubleshooting(self, problem_description: str, machine_name: str = None,
                             error_code: str = None) -> List[Dict[str, Any]]:
        """
        Search for troubleshooting information.
        
        Args:
            problem_description: Description of the problem
            machine_name: Optional machine name
            error_code: Optional error code
            
        Returns:
            Troubleshooting search results
        """
        # Build enhanced query
        query_parts = [problem_description]
        
        if error_code:
            query_parts.append(f"error code {error_code}")
        
        if machine_name:
            query_parts.append(machine_name)
        
        # Add troubleshooting keywords
        query_parts.extend(["troubleshooting", "repair", "fix", "maintenance", "problem"])
        
        enhanced_query = " ".join(query_parts)
        
        # Perform search with preference for manuals and context docs
        results = self.search_documents(
            query=enhanced_query,
            machine_filter=machine_name,
            max_results=15,
            search_type="hybrid"
        )
        
        # Boost scores for relevant document types
        for result in results:
            if result['document_type'] in ['manual', 'context']:
                result['relevance_score'] *= 1.3
            
            # Boost if content contains troubleshooting keywords
            content = result.get('content_cleaned', '').lower()
            troubleshooting_keywords = ['error', 'fault', 'problem', 'fix', 'repair', 'troubleshoot']
            for keyword in troubleshooting_keywords:
                if keyword in content:
                    result['relevance_score'] *= 1.1
                    break
        
        # Re-sort by boosted scores
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results[:10]
    
    def cross_reference_documents(self, machine_name: str, topic: str,
                                document_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Find related information across multiple document types.
        
        Args:
            machine_name: Target machine
            topic: Specific topic to search for
            document_types: Types of documents to search across
            
        Returns:
            Cross-referenced search results
        """
        if document_types is None:
            document_types = ['manual', 'parts', 'diagram', 'context']
        
        all_results = []
        
        for doc_type in document_types:
            results = self.search_documents(
                query=topic,
                machine_filter=machine_name,
                document_type_filter=doc_type,
                max_results=5,
                search_type="hybrid"
            )
            
            # Tag results with their document type
            for result in results:
                result['search_category'] = doc_type
            
            all_results.extend(results)
        
        # Sort by relevance across all document types
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return all_results
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Get machine names that match
            cursor.execute("""
                SELECT DISTINCT machine_name 
                FROM machines 
                WHERE machine_name LIKE ?
                LIMIT 5
            """, (f"%{partial_query}%",))
            
            machine_suggestions = [row[0] for row in cursor.fetchall()]
            
            # Get keywords that match
            cursor.execute("""
                SELECT DISTINCT keyword 
                FROM search_keywords 
                WHERE keyword LIKE ? 
                ORDER BY frequency DESC
                LIMIT 10
            """, (f"%{partial_query}%",))
            
            keyword_suggestions = [row[0] for row in cursor.fetchall()]
            
            # Combine suggestions
            suggestions = machine_suggestions + keyword_suggestions
            return list(set(suggestions))  # Remove duplicates


if __name__ == "__main__":
    # Example usage
    search_engine = DocumentSearchEngine("machine_docs.db")
    
    # Test searches
    test_queries = [
        "CSP separator troubleshooting",
        "feeder operating manual",
        "dryer parts list",
        "error code E001"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching: '{query}'")
        results = search_engine.search_documents(query, max_results=3)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['filename']} (Machine: {result['machine_name']}) - Score: {result['relevance_score']:.3f}")
            if result.get('content_cleaned'):
                preview = result['content_cleaned'][:100] + "..."
                print(f"   Preview: {preview}")