"""MCP server implementation for file indexing and searching."""

import re
from typing import Dict, List, Optional

import mcp
from mcp import Tool, Resource
from mcp.server import Server
from mcp.types import TextContent, ImageContent

from .indexer import FileIndexer
from .models import FileEntry, FileType, IndexStats, SearchQuery


class LibrarianServer:
    """MCP server for file indexing and searching."""
    
    def __init__(self):
        self.server = Server("librarian-mcp-server")
        self.indexer = FileIndexer()
        self.index = None
        
        # Register handlers
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.tool()
        async def search_files(query: str, case_sensitive: bool = False, limit: int = 100) -> str:
            """
            Search for files by name pattern.
            
            Args:
                query: Search pattern (substring match)
                case_sensitive: Whether to perform case-sensitive search
                limit: Maximum number of results to return
            
            Returns:
                List of matching file paths
            """
            if not self.index:
                self.index = self.indexer.get_or_create_index()
            
            results = self.index.search_files(query, case_sensitive)[:limit]
            
            if not results:
                return "No files found matching the pattern."
            
            output = f"Found {len(results)} file(s) matching '{query}':\n\n"
            for file in results:
                output += f"- {file.path} ({file.type.value}, {file.size} bytes)\n"
            
            return output
        
        @self.server.tool()
        async def search_files_regex(pattern: str, case_sensitive: bool = False, limit: int = 100) -> str:
            """
            Search for files using regular expression.
            
            Args:
                pattern: Regular expression pattern
                case_sensitive: Whether to perform case-sensitive search
                limit: Maximum number of results to return
            
            Returns:
                List of matching file paths
            """
            if not self.index:
                self.index = self.indexer.get_or_create_index()
            
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex = re.compile(pattern, flags)
            except re.error as e:
                return f"Invalid regex pattern: {e}"
            
            files = self.index.index.get("files", [])
            results = [f for f in files if regex.search(f.path)][:limit]
            
            if not results:
                return "No files found matching the regex pattern."
            
            output = f"Found {len(results)} file(s) matching regex '{pattern}':\n\n"
            for file in results:
                output += f"- {file.path} ({file.type.value}, {file.size} bytes)\n"
            
            return output
        
        @self.server.tool()
        async def search_by_type(
            file_type: str,
            pattern: Optional[str] = None,
            limit: int = 100
        ) -> str:
            """
            Search for files by type (e.g., python, javascript, typescript).
            
            Args:
                file_type: File type to search for (python, javascript, typescript, kotlin, etc.)
                pattern: Optional name pattern to filter results
                limit: Maximum number of results to return
            
            Returns:
                List of files of the specified type
            """
            if not self.index:
                self.index = self.indexer.get_or_create_index()
            
            # Validate file type
            try:
                ftype = FileType(file_type.lower())
            except ValueError:
                valid_types = ", ".join([t.value for t in FileType])
                return f"Invalid file type. Valid types are: {valid_types}"
            
            # Get files by type
            results = self.index.get_files_by_type(ftype)
            
            # Apply optional pattern filter
            if pattern:
                pattern_lower = pattern.lower()
                results = [f for f in results if pattern_lower in f.path.lower()]
            
            results = results[:limit]
            
            if not results:
                return f"No {file_type} files found."
            
            output = f"Found {len(results)} {file_type} file(s):\n\n"
            for file in results:
                output += f"- {file.path} ({file.size} bytes)\n"
            
            return output
        
        @self.server.tool()
        async def refresh_index() -> str:
            """
            Refresh the file index by rescanning the repository.
            
            Returns:
                Status message with indexing results
            """
            self.index = self.indexer.refresh_index()
            self.indexer.save_index(self.index)
            
            return (
                f"Index refreshed successfully!\n"
                f"Repository: {self.index.repository.path}\n"
                f"Total files: {self.index.repository.total_files}\n"
                f"Last updated: {self.index.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        @self.server.tool()
        async def get_index_stats() -> str:
            """
            Get statistics about the current file index.
            
            Returns:
                Index statistics including file counts by type
            """
            if not self.index:
                self.index = self.indexer.get_or_create_index()
            
            # Calculate stats by file type
            type_counts: Dict[FileType, int] = {}
            total_size = 0
            
            for file in self.index.index.get("files", []):
                type_counts[file.type] = type_counts.get(file.type, 0) + 1
                total_size += file.size
            
            output = f"Index Statistics:\n"
            output += f"================\n\n"
            output += f"Repository: {self.index.repository.path}\n"
            output += f"Total files: {self.index.repository.total_files}\n"
            output += f"Total size: {total_size:,} bytes\n"
            output += f"Last updated: {self.index.last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            output += "Files by type:\n"
            for file_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                output += f"  - {file_type.value}: {count}\n"
            
            return output
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.server.resource("index://stats")
        async def get_stats_resource() -> str:
            """Get current index statistics as a resource."""
            if not self.index:
                self.index = self.indexer.get_or_create_index()
            
            type_counts: Dict[FileType, int] = {}
            total_size = 0
            
            for file in self.index.index.get("files", []):
                type_counts[file.type] = type_counts.get(file.type, 0) + 1
                total_size += file.size
            
            stats = IndexStats(
                total_files=self.index.repository.total_files,
                total_size=total_size,
                file_types=type_counts,
                last_updated=self.index.last_updated,
                index_path=str(self.indexer.index_path)
            )
            
            return stats.model_dump_json(indent=2)
        
        @self.server.resource("index://config")
        async def get_config_resource() -> str:
            """Get server configuration."""
            config = {
                "repository_path": str(self.indexer.repo_path),
                "index_path": str(self.indexer.index_path),
                "version": "0.1.0",
                "supported_file_types": [t.value for t in FileType]
            }
            
            import json
            return json.dumps(config, indent=2)
    
    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        
        print("Starting Librarian MCP Server...")
        print(f"Repository: {self.indexer.repo_path}")
        
        # Initialize index on startup
        self.index = self.indexer.get_or_create_index()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )