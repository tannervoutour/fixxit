"""SQL query validation and sanitization for security."""

import re
import sqlite3
from typing import List, Optional, Tuple


class QueryValidator:
    """Validates and sanitizes SQL queries for safety."""
    
    # Allowed SQL keywords for SELECT operations
    ALLOWED_KEYWORDS = {
        'select', 'from', 'where', 'join', 'inner', 'left', 'right', 'outer',
        'on', 'and', 'or', 'not', 'in', 'like', 'between', 'is', 'null',
        'order', 'by', 'group', 'having', 'limit', 'offset', 'as', 'distinct',
        'count', 'sum', 'avg', 'min', 'max', 'case', 'when', 'then', 'else', 'end'
    }
    
    # Dangerous keywords that should never be allowed
    FORBIDDEN_KEYWORDS = {
        'drop', 'delete', 'insert', 'update', 'create', 'alter', 'truncate',
        'replace', 'merge', 'exec', 'execute', 'sp_', 'xp_', 'schema',
        'information_schema', 'sys', 'master', 'msdb', 'tempdb'
    }
    
    def __init__(self):
        """Initialize the query validator."""
        # Compile regex patterns for efficiency
        self.comment_pattern = re.compile(r'--.*$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
        self.semicolon_pattern = re.compile(r';(?!\s*$)')  # Semicolons not at end
        self.keyword_pattern = re.compile(r'\b(' + '|'.join(self.FORBIDDEN_KEYWORDS) + r')\b', re.IGNORECASE)
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a query is safe to execute.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        # Remove comments and normalize whitespace
        cleaned_query = self._clean_query(query)
        
        # Check for multiple statements
        if self._has_multiple_statements(cleaned_query):
            return False, "Multiple statements not allowed"
        
        # Check for forbidden keywords
        forbidden_match = self.keyword_pattern.search(cleaned_query)
        if forbidden_match:
            return False, f"Forbidden keyword detected: {forbidden_match.group(1)}"
        
        # Ensure query starts with SELECT
        if not self._starts_with_select(cleaned_query):
            return False, "Only SELECT queries are allowed"
        
        # Check for SQL injection patterns
        injection_check = self._check_injection_patterns(cleaned_query)
        if not injection_check[0]:
            return False, injection_check[1]
        
        return True, None
    
    def _clean_query(self, query: str) -> str:
        """Remove comments and normalize whitespace."""
        # Remove SQL comments
        cleaned = self.comment_pattern.sub(' ', query)
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _has_multiple_statements(self, query: str) -> bool:
        """Check if query contains multiple statements."""
        # Look for semicolons that aren't at the very end
        return bool(self.semicolon_pattern.search(query))
    
    def _starts_with_select(self, query: str) -> bool:
        """Check if query starts with SELECT keyword."""
        return query.lower().startswith('select')
    
    def _check_injection_patterns(self, query: str) -> Tuple[bool, Optional[str]]:
        """Check for common SQL injection patterns."""
        injection_patterns = [
            (r'\bunion\s+select\b', "UNION SELECT detected"),
            (r'\bor\s+1\s*=\s*1\b', "OR 1=1 pattern detected"),
            (r'\bor\s+\'.*\'\s*=\s*\'.*\'\b', "OR string comparison detected"),
            (r';\s*(drop|delete|insert|update)', "Dangerous statement after semicolon"),
            (r'\binto\s+outfile\b', "INTO OUTFILE detected"),
            (r'\bload_file\s*\(', "LOAD_FILE function detected"),
            (r'\bchar\s*\(\s*\d+\s*\)', "CHAR() function detected (possible bypass)"),
        ]
        
        query_lower = query.lower()
        for pattern, message in injection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return False, message
        
        return True, None
    
    def sanitize_table_name(self, table_name: str) -> str:
        """Sanitize table name to prevent injection."""
        # Only allow alphanumeric characters and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', table_name)
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'table_' + sanitized
        
        return sanitized
    
    def get_allowed_tables(self) -> List[str]:
        """Get list of allowed table names for this system."""
        return [
            'machines',
            'technicians', 
            'fault_codes',
            'maintenance_records',
            'trouble_tickets',
            'parts_inventory'
        ]
    
    def validate_table_access(self, table_name: str) -> bool:
        """Check if access to a table is allowed."""
        sanitized_name = self.sanitize_table_name(table_name)
        return sanitized_name in self.get_allowed_tables()


# Global validator instance
query_validator = QueryValidator()