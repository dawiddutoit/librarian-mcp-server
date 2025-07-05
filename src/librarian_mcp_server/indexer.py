"""File indexing logic for repository scanning."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

import yaml
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from .models import FileEntry, RepositoryInfo, WorkspaceIndex, get_file_type


class FileIndexer:
    """Handles file indexing and workspace management."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize the indexer with repository path."""
        self.repo_path = repo_path or self._find_repo_root()
        self.index_path = self.repo_path / ".claude" / "workspace" / "workspace.yml"
        self._gitignore_spec = self._load_gitignore()
    
    def _find_repo_root(self) -> Path:
        """Find the repository root by looking for .git directory."""
        current = Path.cwd()
        
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        
        # If no .git found, use current directory
        return Path.cwd()
    
    def _load_gitignore(self) -> Optional[PathSpec]:
        """Load .gitignore patterns if available."""
        gitignore_path = self.repo_path / ".gitignore"
        if not gitignore_path.exists():
            return None
        
        with open(gitignore_path, "r", encoding="utf-8") as f:
            patterns = [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
        
        # Always ignore .git and .claude directories
        patterns.extend([".git/", ".claude/"])
        
        return PathSpec.from_lines(GitWildMatchPattern, patterns)
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        if self._gitignore_spec:
            # Get relative path from repo root
            try:
                rel_path = path.relative_to(self.repo_path)
                return self._gitignore_spec.match_file(str(rel_path))
            except ValueError:
                # Path is outside repo
                return True
        
        # Always ignore hidden files and common non-source directories
        if any(part.startswith(".") for part in path.parts):
            return True
        
        ignore_dirs = {"node_modules", "__pycache__", "venv", "env", "build", "dist", "target"}
        if any(part in ignore_dirs for part in path.parts):
            return True
        
        return False
    
    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            # Return empty hash for files we can't read
            return ""
    
    def _scan_directory(self, directory: Path) -> List[FileEntry]:
        """Recursively scan directory for files."""
        files = []
        
        try:
            for item in directory.iterdir():
                if self._should_ignore(item):
                    continue
                
                if item.is_file():
                    try:
                        stat = item.stat()
                        rel_path = item.relative_to(self.repo_path)
                        
                        file_entry = FileEntry(
                            path=str(rel_path),
                            type=get_file_type(item),
                            size=stat.st_size,
                            modified=datetime.fromtimestamp(stat.st_mtime),
                            hash=self._hash_file(item)
                        )
                        files.append(file_entry)
                    except Exception:
                        # Skip files we can't process
                        continue
                
                elif item.is_dir():
                    files.extend(self._scan_directory(item))
        
        except PermissionError:
            # Skip directories we can't access
            pass
        
        return files
    
    def create_index(self) -> WorkspaceIndex:
        """Create a new index by scanning the repository."""
        print(f"Indexing repository at: {self.repo_path}")
        
        # Scan all files
        files = self._scan_directory(self.repo_path)
        
        # Create repository info
        repo_info = RepositoryInfo(
            path=str(self.repo_path.absolute()),
            total_files=len(files)
        )
        
        # Create workspace index
        index = WorkspaceIndex(
            last_updated=datetime.now(),
            repository=repo_info
        )
        
        # Add files to index
        for file_entry in files:
            index.add_file(file_entry)
        
        print(f"Indexed {len(files)} files")
        return index
    
    def save_index(self, index: WorkspaceIndex) -> None:
        """Save index to workspace.yml file."""
        # Ensure directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and save as YAML
        index_dict = index.model_dump()
        
        with open(self.index_path, "w", encoding="utf-8") as f:
            yaml.dump(index_dict, f, default_flow_style=False, sort_keys=False)
        
        print(f"Index saved to: {self.index_path}")
    
    def load_index(self) -> Optional[WorkspaceIndex]:
        """Load existing index from workspace.yml."""
        if not self.index_path.exists():
            return None
        
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            # Convert string dates back to datetime
            if "last_updated" in data:
                data["last_updated"] = datetime.fromisoformat(data["last_updated"])
            
            if "index" in data and "files" in data["index"]:
                for file_data in data["index"]["files"]:
                    if "modified" in file_data:
                        file_data["modified"] = datetime.fromisoformat(file_data["modified"])
            
            return WorkspaceIndex(**data)
        
        except Exception as e:
            print(f"Error loading index: {e}")
            return None
    
    def refresh_index(self) -> WorkspaceIndex:
        """Refresh the index by rescanning the repository."""
        return self.create_index()
    
    def get_or_create_index(self) -> WorkspaceIndex:
        """Get existing index or create a new one."""
        index = self.load_index()
        
        if index is None:
            print("No existing index found. Creating new index...")
            index = self.create_index()
            self.save_index(index)
        else:
            print(f"Loaded existing index with {index.repository.total_files} files")
        
        return index