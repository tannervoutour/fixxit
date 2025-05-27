"""Configuration settings for the MCP SQLite server."""

import os
from pathlib import Path
from typing import Optional


class ServerConfig:
    """Configuration class for the MCP SQLite maintenance server."""
    
    # Server identification
    SERVER_NAME = "SQLite Maintenance Database"
    SERVER_VERSION = "1.0.0"
    SERVER_DESCRIPTION = "MCP server providing access to machine maintenance database"
    
    # Database configuration
    DEFAULT_DB_PATH = Path(__file__).parent / "database" / "database.db"
    
    # Query limits
    MAX_QUERY_RESULTS = 1000
    DEFAULT_QUERY_LIMIT = 100
    MAX_RESOURCE_SAMPLE_SIZE = 10
    
    # Security settings
    ALLOW_CUSTOM_QUERIES = True  # Allow execute_query tool
    READ_ONLY_MODE = True  # Only SELECT operations allowed
    
    # Performance settings
    CONNECTION_TIMEOUT = 30  # seconds
    QUERY_TIMEOUT = 60  # seconds
    
    @classmethod
    def get_database_path(cls) -> Path:
        """Get the database path, checking environment variable first."""
        env_path = os.getenv("MCP_DB_PATH")
        if env_path:
            return Path(env_path)
        return cls.DEFAULT_DB_PATH
    
    @classmethod
    def get_server_info(cls) -> dict:
        """Get server information dictionary."""
        return {
            "name": cls.SERVER_NAME,
            "version": cls.SERVER_VERSION,
            "description": cls.SERVER_DESCRIPTION,
            "database_path": str(cls.get_database_path()),
            "read_only": cls.READ_ONLY_MODE
        }


# Global configuration instance
config = ServerConfig()