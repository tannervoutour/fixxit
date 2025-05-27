#!/usr/bin/env python3
"""
MCP Tools for Machine Documentation Search
Provides search and retrieval tools for the machine documentation database.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from search_engine import DocumentSearchEngine


class DocumentSearchTools:
    """MCP-compatible tools for machine documentation search."""
    
    def __init__(self, database_path: str = None):
        """Initialize the document search tools."""
        if database_path is None:
            database_path = str(Path(__file__).parent / "machine_docs.db")
        
        self.search_engine = DocumentSearchEngine(database_path)
        self.logger = logging.getLogger('DocumentSearchTools')
    
    def search_machine_documents(self, query: str, machine_name: str = None, 
                                document_type: str = None, max_results: int = 10) -> str:
        """
        Search through machine documentation by keywords or natural language query.
        
        Args:
            query: Natural language search query about machines or procedures
            machine_name: Optional filter by specific machine name (e.g., 'CSP', 'Feeder_1')
            document_type: Optional filter by document type ('manual', 'diagram', 'parts', 'context', 'general')
            max_results: Maximum number of results to return (default 10)
            
        Returns:
            JSON string with search results including document references and page numbers
        """
        try:
            results = self.search_engine.search_documents(
                query=query,
                machine_filter=machine_name,
                document_type_filter=document_type,
                max_results=max_results,
                search_type="hybrid"
            )
            
            # Format results for AI consumption
            formatted_results = []
            for result in results:
                formatted_result = {
                    "document_id": result.get('document_id'),
                    "filename": result.get('filename'),
                    "machine_name": result.get('machine_name'),
                    "document_type": result.get('document_type'),
                    "page_number": result.get('page_number', 1),
                    "relevance_score": round(result.get('relevance_score', 0), 3),
                    "content_preview": self._create_content_preview(result.get('content_cleaned', '')),
                    "file_path": result.get('file_path'),
                    "section_title": result.get('section_title')
                }
                formatted_results.append(formatted_result)
            
            return json.dumps({
                "success": True,
                "query": query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "filters_applied": {
                    "machine_name": machine_name,
                    "document_type": document_type
                }
            }, indent=2)
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "query": query
            })
    
    def get_document_content(self, document_id: int, page_numbers: str = None) -> str:
        """
        Retrieve specific pages or sections from a document.
        
        Args:
            document_id: Document identifier from search results
            page_numbers: Comma-separated page numbers to retrieve (e.g., '1,3,5' or 'all')
            
        Returns:
            JSON string with document content and metadata
        """
        try:
            # Parse page numbers
            pages_to_get = None
            if page_numbers and page_numbers.lower() != 'all':
                try:
                    pages_to_get = [int(p.strip()) for p in page_numbers.split(',')]
                except ValueError:
                    return json.dumps({
                        "success": False,
                        "error": f"Invalid page numbers format: {page_numbers}. Use comma-separated numbers or 'all'"
                    })
            
            result = self.search_engine.get_document_content(document_id, pages_to_get)
            
            if "error" in result:
                return json.dumps({
                    "success": False,
                    "error": result["error"]
                })
            
            # Format document content
            formatted_result = {
                "success": True,
                "document": {
                    "id": result["document"]["id"],
                    "filename": result["document"]["filename"],
                    "machine_name": result["document"]["machine_name"],
                    "document_type": result["document"]["document_type"],
                    "title": result["document"].get("title"),
                    "file_path": result["document"]["file_path"],
                    "total_pages": result["document"]["page_count"]
                },
                "content": []
            }
            
            for page in result["pages"]:
                page_content = {
                    "page_number": page["page_number"],
                    "content": page["content_cleaned"],
                    "section_title": page.get("section_title"),
                    "keywords": page.get("keywords"),
                    "word_count": page.get("word_count", 0)
                }
                formatted_result["content"].append(page_content)
            
            return json.dumps(formatted_result, indent=2)
            
        except Exception as e:
            self.logger.error(f"Content retrieval failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "document_id": document_id
            })
    
    def get_machine_overview(self, machine_name: str, include_context: bool = True, 
                           include_diagrams: bool = True) -> str:
        """
        Get comprehensive overview of a specific machine with available documentation.
        
        Args:
            machine_name: Name of the machine (e.g., 'CSP', 'Feeder_1', 'PowerPress')
            include_context: Include pinned context information (default True)
            include_diagrams: Include diagram references (default True)
            
        Returns:
            JSON string with machine overview and document summary
        """
        try:
            result = self.search_engine.get_machine_overview(
                machine_name=machine_name,
                include_context=include_context,
                include_diagrams=include_diagrams
            )
            
            if "error" in result:
                return json.dumps({
                    "success": False,
                    "error": result["error"],
                    "machine_name": machine_name
                })
            
            # Format the overview
            formatted_result = {
                "success": True,
                "machine": {
                    "name": result["machine"]["machine_name"],
                    "type": result["machine"]["machine_type"],
                    "line": result["machine"]["line_number"],
                    "description": result["machine"]["description"],
                    "directory": result["machine"]["directory_path"]
                },
                "document_summary": result["document_summary"],
                "available_documents": {
                    "total": sum(doc["count"] for doc in result["document_summary"]),
                    "by_type": {doc["document_type"]: doc["count"] for doc in result["document_summary"]}
                }
            }
            
            if include_context and result["context_documents"]:
                formatted_result["context_information"] = []
                for doc in result["context_documents"]:
                    context_info = {
                        "filename": doc["filename"],
                        "content": self._create_content_preview(doc.get("content_cleaned", ""), max_length=500)
                    }
                    formatted_result["context_information"].append(context_info)
            
            if include_diagrams and result["diagram_references"]:
                formatted_result["diagram_references"] = [
                    {
                        "filename": doc["filename"],
                        "title": doc.get("title", ""),
                        "file_path": doc["file_path"]
                    }
                    for doc in result["diagram_references"]
                ]
            
            return json.dumps(formatted_result, indent=2)
            
        except Exception as e:
            self.logger.error(f"Machine overview failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "machine_name": machine_name
            })
    
    def search_troubleshooting_info(self, problem_description: str, machine_name: str = None,
                                  error_code: str = None) -> str:
        """
        Search for troubleshooting procedures and error solutions.
        
        Args:
            problem_description: Description of the problem or issue
            machine_name: Optional specific machine name
            error_code: Optional specific error code to look up
            
        Returns:
            JSON string with troubleshooting information and procedures
        """
        try:
            results = self.search_engine.search_troubleshooting(
                problem_description=problem_description,
                machine_name=machine_name,
                error_code=error_code
            )
            
            formatted_results = []
            for result in results:
                formatted_result = {
                    "document_id": result.get('document_id'),
                    "filename": result.get('filename'),
                    "machine_name": result.get('machine_name'),
                    "document_type": result.get('document_type'),
                    "page_number": result.get('page_number', 1),
                    "relevance_score": round(result.get('relevance_score', 0), 3),
                    "content_preview": self._create_content_preview(result.get('content_cleaned', '')),
                    "section_title": result.get('section_title'),
                    "file_path": result.get('file_path')
                }
                formatted_results.append(formatted_result)
            
            return json.dumps({
                "success": True,
                "problem_description": problem_description,
                "search_parameters": {
                    "machine_name": machine_name,
                    "error_code": error_code
                },
                "total_results": len(formatted_results),
                "troubleshooting_info": formatted_results
            }, indent=2)
            
        except Exception as e:
            self.logger.error(f"Troubleshooting search failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "problem_description": problem_description
            })
    
    def cross_reference_machine_docs(self, machine_name: str, topic: str, 
                                   document_types: str = None) -> str:
        """
        Find related information across multiple document types for a machine.
        
        Args:
            machine_name: Target machine name
            topic: Specific topic to search for (e.g., 'maintenance', 'parts', 'wiring')
            document_types: Comma-separated document types to search ('manual,parts,diagram,context')
            
        Returns:
            JSON string with cross-referenced information from multiple document types
        """
        try:
            # Parse document types
            doc_types = None
            if document_types:
                doc_types = [dt.strip() for dt in document_types.split(',')]
            
            results = self.search_engine.cross_reference_documents(
                machine_name=machine_name,
                topic=topic,
                document_types=doc_types
            )
            
            # Group results by document type
            grouped_results = {}
            for result in results:
                doc_type = result.get('search_category', result.get('document_type', 'unknown'))
                if doc_type not in grouped_results:
                    grouped_results[doc_type] = []
                
                formatted_result = {
                    "document_id": result.get('document_id'),
                    "filename": result.get('filename'),
                    "page_number": result.get('page_number', 1),
                    "relevance_score": round(result.get('relevance_score', 0), 3),
                    "content_preview": self._create_content_preview(result.get('content_cleaned', '')),
                    "section_title": result.get('section_title'),
                    "file_path": result.get('file_path')
                }
                grouped_results[doc_type].append(formatted_result)
            
            return json.dumps({
                "success": True,
                "machine_name": machine_name,
                "topic": topic,
                "document_types_searched": list(grouped_results.keys()),
                "total_results": len(results),
                "results_by_type": grouped_results
            }, indent=2)
            
        except Exception as e:
            self.logger.error(f"Cross-reference search failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "machine_name": machine_name,
                "topic": topic
            })
    
    def get_document_suggestions(self, partial_query: str) -> str:
        """
        Get search suggestions based on partial query input.
        
        Args:
            partial_query: Partial search query to get suggestions for
            
        Returns:
            JSON string with suggested completions and related terms
        """
        try:
            suggestions = self.search_engine.get_search_suggestions(partial_query)
            
            return json.dumps({
                "success": True,
                "partial_query": partial_query,
                "suggestions": suggestions,
                "total_suggestions": len(suggestions)
            }, indent=2)
            
        except Exception as e:
            self.logger.error(f"Suggestions failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "partial_query": partial_query
            })
    
    def _create_content_preview(self, content: str, max_length: int = 200) -> str:
        """Create a preview of content with truncation."""
        if not content:
            return ""
        
        content = content.strip()
        if len(content) <= max_length:
            return content
        
        # Find a good breaking point near the max length
        truncated = content[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # If we can break at a reasonable point
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."


# Tool function definitions for MCP integration
def search_machine_documents(query: str, machine_name: str = None, 
                           document_type: str = None, max_results: int = 10) -> str:
    """Search through machine documentation by keywords or natural language query."""
    tools = DocumentSearchTools()
    return tools.search_machine_documents(query, machine_name, document_type, max_results)


def get_document_content(document_id: int, page_numbers: str = None) -> str:
    """Retrieve specific pages or sections from a document."""
    tools = DocumentSearchTools()
    return tools.get_document_content(document_id, page_numbers)


def get_machine_overview(machine_name: str, include_context: bool = True, 
                        include_diagrams: bool = True) -> str:
    """Get comprehensive overview of a specific machine with available documentation."""
    tools = DocumentSearchTools()
    return tools.get_machine_overview(machine_name, include_context, include_diagrams)


def search_troubleshooting_info(problem_description: str, machine_name: str = None,
                               error_code: str = None) -> str:
    """Search for troubleshooting procedures and error solutions."""
    tools = DocumentSearchTools()
    return tools.search_troubleshooting_info(problem_description, machine_name, error_code)


def cross_reference_machine_docs(machine_name: str, topic: str, 
                                document_types: str = None) -> str:
    """Find related information across multiple document types for a machine."""
    tools = DocumentSearchTools()
    return tools.cross_reference_machine_docs(machine_name, topic, document_types)


def get_document_suggestions(partial_query: str) -> str:
    """Get search suggestions based on partial query input."""
    tools = DocumentSearchTools()
    return tools.get_document_suggestions(partial_query)


if __name__ == "__main__":
    # Test the tools
    tools = DocumentSearchTools()
    
    # Test search
    print("Testing document search...")
    result = tools.search_machine_documents("CSP separator operating", max_results=3)
    print(result)
    
    print("\nTesting machine overview...")
    result = tools.get_machine_overview("CSP")
    print(result)