"""Pydantic models for the file index structure."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Supported file types for categorization."""
    
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    KOTLIN = "kotlin"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    HTML = "html"
    CSS = "css"
    OTHER = "other"


FILE_TYPE_EXTENSIONS: Dict[FileType, List[str]] = {
    FileType.PYTHON: [".py", ".pyi", ".pyx", ".pxd"],
    FileType.JAVASCRIPT: [".js", ".mjs", ".cjs"],
    FileType.TYPESCRIPT: [".ts", ".tsx", ".d.ts"],
    FileType.KOTLIN: [".kt", ".kts"],
    FileType.JAVA: [".java"],
    FileType.GO: [".go"],
    FileType.RUST: [".rs"],
    FileType.CPP: [".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".h++"],
    FileType.C: [".c", ".h"],
    FileType.CSHARP: [".cs"],
    FileType.RUBY: [".rb"],
    FileType.PHP: [".php"],
    FileType.SWIFT: [".swift"],
    FileType.MARKDOWN: [".md", ".markdown"],
    FileType.JSON: [".json"],
    FileType.YAML: [".yml", ".yaml"],
    FileType.XML: [".xml"],
    FileType.HTML: [".html", ".htm"],
    FileType.CSS: [".css", ".scss", ".sass", ".less"],
}


def get_file_type(file_path: Path) -> FileType:
    """Determine the file type based on extension."""
    ext = file_path.suffix.lower()
    
    for file_type, extensions in FILE_TYPE_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    
    return FileType.OTHER


class FileEntry(BaseModel):
    """Represents a single indexed file."""
    
    path: str = Field(description="Relative path from repository root")
    type: FileType = Field(description="File type classification")
    size: int = Field(description="File size in bytes")
    modified: datetime = Field(description="Last modification time")
    hash: str = Field(description="SHA256 hash of file content")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RepositoryInfo(BaseModel):
    """Repository metadata."""
    
    path: str = Field(description="Absolute path to repository")
    total_files: int = Field(description="Total number of indexed files")


class WorkspaceIndex(BaseModel):
    """Complete workspace index structure."""
    
    version: str = Field(default="1.0", description="Index format version")
    last_updated: datetime = Field(description="Last index update time")
    repository: RepositoryInfo
    index: Dict[str, List[FileEntry]] = Field(
        default_factory=lambda: {"files": []},
        description="Indexed files"
    )
    file_types: Dict[FileType, List[str]] = Field(
        default_factory=lambda: FILE_TYPE_EXTENSIONS.copy(),
        description="File type to extension mapping"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_file(self, file_entry: FileEntry):
        """Add a file to the index."""
        if "files" not in self.index:
            self.index["files"] = []
        self.index["files"].append(file_entry)
        self.repository.total_files = len(self.index["files"])
    
    def get_files_by_type(self, file_type: FileType) -> List[FileEntry]:
        """Get all files of a specific type."""
        return [
            f for f in self.index.get("files", [])
            if f.type == file_type
        ]
    
    def search_files(self, pattern: str, case_sensitive: bool = False) -> List[FileEntry]:
        """Search files by name pattern."""
        files = self.index.get("files", [])
        if not case_sensitive:
            pattern = pattern.lower()
            return [
                f for f in files
                if pattern in f.path.lower()
            ]
        return [
            f for f in files
            if pattern in f.path
        ]


class SearchQuery(BaseModel):
    """Search query parameters."""
    
    pattern: Optional[str] = Field(None, description="Search pattern")
    regex: Optional[str] = Field(None, description="Regex pattern")
    file_type: Optional[FileType] = Field(None, description="Filter by file type")
    case_sensitive: bool = Field(False, description="Case-sensitive search")
    limit: int = Field(100, description="Maximum results to return")


class IndexStats(BaseModel):
    """Index statistics."""
    
    total_files: int
    total_size: int
    file_types: Dict[FileType, int]
    last_updated: datetime
    index_path: str