"""Input validation utilities for the OpenAI MCP client."""

import re
from typing import Any, Dict, List, Optional, Tuple


class InputValidator:
    """Validates user inputs and function parameters."""
    
    @staticmethod
    def validate_machine_status(status: str) -> bool:
        """Validate machine status values."""
        valid_statuses = {'operational', 'maintenance', 'down', 'retired'}
        return status.lower() in valid_statuses
    
    @staticmethod
    def validate_ticket_status(status: str) -> bool:
        """Validate trouble ticket status values."""
        valid_statuses = {'open', 'assigned', 'in_progress', 'resolved', 'closed'}
        return status.lower() in valid_statuses
    
    @staticmethod
    def validate_priority(priority: str) -> bool:
        """Validate priority values."""
        valid_priorities = {'low', 'medium', 'high', 'urgent'}
        return priority.lower() in valid_priorities
    
    @staticmethod
    def validate_maintenance_type(maintenance_type: str) -> bool:
        """Validate maintenance type values."""
        valid_types = {'preventive', 'corrective', 'emergency', 'inspection'}
        return maintenance_type.lower() in valid_types
    
    @staticmethod
    def validate_certification_level(level: str) -> bool:
        """Validate technician certification levels."""
        valid_levels = {'junior', 'senior', 'expert', 'lead'}
        return level.lower() in valid_levels
    
    @staticmethod
    def validate_sql_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety (basic validation).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        query_lower = query.lower().strip()
        
        # Must start with SELECT
        if not query_lower.startswith('select'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        dangerous_keywords = [
            'drop', 'delete', 'insert', 'update', 'create', 'alter', 
            'truncate', 'replace', 'merge', 'exec', 'execute'
        ]
        
        for keyword in dangerous_keywords:
            if f' {keyword} ' in f' {query_lower} ':
                return False, f"Dangerous keyword '{keyword}' not allowed"
        
        # Check for multiple statements (semicolons not at end)
        if ';' in query[:-1]:  # Allow semicolon at very end
            return False, "Multiple statements not allowed"
        
        return True, None
    
    @staticmethod
    def validate_function_parameters(function_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters for a specific function.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        validators = {
            'search_equipment': InputValidator._validate_search_equipment_params,
            'get_maintenance_tickets': InputValidator._validate_tickets_params,
            'get_service_history': InputValidator._validate_service_history_params,
            'search_parts_inventory': InputValidator._validate_parts_params,
            'get_troubleshooting_help': InputValidator._validate_fault_code_params,
            'get_technician_info': InputValidator._validate_technician_params,
            'query_maintenance_database': InputValidator._validate_query_params,
            'get_database_overview': InputValidator._validate_overview_params
        }
        
        validator = validators.get(function_name)
        if not validator:
            return True, None  # No specific validation
        
        return validator(parameters)
    
    @staticmethod
    def _validate_search_equipment_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate search equipment parameters."""
        if 'status' in params:
            if not InputValidator.validate_machine_status(params['status']):
                return False, f"Invalid machine status: {params['status']}"
        
        # Location, model, manufacturer can be any string
        return True, None
    
    @staticmethod
    def _validate_tickets_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate ticket parameters."""
        if 'status' in params:
            if not InputValidator.validate_ticket_status(params['status']):
                return False, f"Invalid ticket status: {params['status']}"
        
        if 'priority' in params:
            if not InputValidator.validate_priority(params['priority']):
                return False, f"Invalid priority: {params['priority']}"
        
        if 'machine_id' in params:
            try:
                machine_id = int(params['machine_id'])
                if machine_id <= 0:
                    return False, "Machine ID must be positive"
            except (ValueError, TypeError):
                return False, "Machine ID must be a number"
        
        if 'limit' in params:
            try:
                limit = int(params['limit'])
                if limit <= 0 or limit > 1000:
                    return False, "Limit must be between 1 and 1000"
            except (ValueError, TypeError):
                return False, "Limit must be a number"
        
        return True, None
    
    @staticmethod
    def _validate_service_history_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate service history parameters."""
        if 'machine_id' in params:
            try:
                machine_id = int(params['machine_id'])
                if machine_id <= 0:
                    return False, "Machine ID must be positive"
            except (ValueError, TypeError):
                return False, "Machine ID must be a number"
        
        if 'technician_id' in params:
            try:
                tech_id = int(params['technician_id'])
                if tech_id <= 0:
                    return False, "Technician ID must be positive"
            except (ValueError, TypeError):
                return False, "Technician ID must be a number"
        
        if 'maintenance_type' in params:
            if not InputValidator.validate_maintenance_type(params['maintenance_type']):
                return False, f"Invalid maintenance type: {params['maintenance_type']}"
        
        if 'days_back' in params:
            try:
                days = int(params['days_back'])
                if days <= 0 or days > 365:
                    return False, "Days back must be between 1 and 365"
            except (ValueError, TypeError):
                return False, "Days back must be a number"
        
        return True, None
    
    @staticmethod
    def _validate_parts_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate parts search parameters."""
        if 'low_stock_only' in params:
            if not isinstance(params['low_stock_only'], bool):
                return False, "low_stock_only must be true or false"
        
        # part_number, name, compatible_model can be any string
        return True, None
    
    @staticmethod
    def _validate_fault_code_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate fault code parameters."""
        if 'fault_code' in params:
            code = params['fault_code']
            if not isinstance(code, str) or not code.strip():
                return False, "Fault code must be a non-empty string"
            
            # Basic format validation (letter followed by digits)
            if not re.match(r'^[A-Z]\d{3}$', code.upper()):
                return False, "Fault code must be in format like 'E001', 'H001', etc."
        
        return True, None
    
    @staticmethod
    def _validate_technician_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate technician parameters."""
        if 'technician_id' in params:
            try:
                tech_id = int(params['technician_id'])
                if tech_id <= 0:
                    return False, "Technician ID must be positive"
            except (ValueError, TypeError):
                return False, "Technician ID must be a number"
        
        return True, None
    
    @staticmethod
    def _validate_query_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate custom query parameters."""
        if 'query' not in params:
            return False, "Query parameter is required"
        
        query = params['query']
        if not isinstance(query, str):
            return False, "Query must be a string"
        
        is_valid, error = InputValidator.validate_sql_query(query)
        if not is_valid:
            return False, error
        
        if 'limit' in params:
            try:
                limit = int(params['limit'])
                if limit <= 0 or limit > 1000:
                    return False, "Limit must be between 1 and 1000"
            except (ValueError, TypeError):
                return False, "Limit must be a number"
        
        return True, None
    
    @staticmethod
    def _validate_overview_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate overview parameters (none required)."""
        return True, None
    
    @staticmethod
    def sanitize_string_input(input_str: str) -> str:
        """Sanitize string input to prevent issues."""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>&"\'`]', '', input_str)
        
        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_user_input(user_input: str) -> Tuple[bool, Optional[str]]:
        """Validate general user input."""
        if not user_input or not user_input.strip():
            return False, "Input cannot be empty"
        
        if len(user_input) > 2000:
            return False, "Input too long (max 2000 characters)"
        
        # Check for obvious injection attempts
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\('
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, "Input contains suspicious content"
        
        return True, None


# Global validator instance
validator = InputValidator()