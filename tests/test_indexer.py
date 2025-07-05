"""Tests for the file indexer."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from librarian_mcp_server.indexer import FileIndexer
from librarian_mcp_server.models import FileType, WorkspaceIndex


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create .git directory to simulate a repository
        (repo_path / ".git").mkdir()
        
        # Create test files
        (repo_path / "src").mkdir()
        (repo_path / "src" / "main.py").write_text("print('hello')")
        (repo_path / "src" / "utils.py").write_text("def helper(): pass")
        
        (repo_path / "js").mkdir()
        (repo_path / "js" / "app.js").write_text("console.log('test')")
        (repo_path / "js" / "component.tsx").write_text("export default Component")
        
        # Create files that should be ignored
        (repo_path / ".gitignore").write_text("*.log\nnode_modules/\n")
        (repo_path / "test.log").write_text("log content")
        
        (repo_path / "node_modules").mkdir()
        (repo_path / "node_modules" / "package.js").write_text("module")
        
        yield repo_path


def test_indexer_initialization(temp_repo):
    """Test indexer initialization and repo detection."""
    indexer = FileIndexer(temp_repo)
    assert indexer.repo_path == temp_repo
    assert indexer.index_path == temp_repo / ".claude" / "workspace" / "workspace.yml"


def test_create_index(temp_repo):
    """Test index creation."""
    indexer = FileIndexer(temp_repo)
    index = indexer.create_index()
    
    assert isinstance(index, WorkspaceIndex)
    assert index.repository.path == str(temp_repo.absolute())
    
    # Check that correct files were indexed
    files = index.index["files"]
    file_paths = [f.path for f in files]
    
    assert "src/main.py" in file_paths
    assert "src/utils.py" in file_paths
    assert "js/app.js" in file_paths
    assert "js/component.tsx" in file_paths
    
    # Check that ignored files were not indexed
    assert "test.log" not in file_paths
    assert "node_modules/package.js" not in file_paths
    assert ".gitignore" not in file_paths


def test_file_type_detection(temp_repo):
    """Test file type detection."""
    indexer = FileIndexer(temp_repo)
    index = indexer.create_index()
    
    files = {f.path: f for f in index.index["files"]}
    
    assert files["src/main.py"].type == FileType.PYTHON
    assert files["src/utils.py"].type == FileType.PYTHON
    assert files["js/app.js"].type == FileType.JAVASCRIPT
    assert files["js/component.tsx"].type == FileType.TYPESCRIPT


def test_save_and_load_index(temp_repo):
    """Test saving and loading index."""
    indexer = FileIndexer(temp_repo)
    
    # Create and save index
    original_index = indexer.create_index()
    indexer.save_index(original_index)
    
    # Load index
    loaded_index = indexer.load_index()
    
    assert loaded_index is not None
    assert loaded_index.repository.total_files == original_index.repository.total_files
    assert len(loaded_index.index["files"]) == len(original_index.index["files"])
    
    # Compare file entries
    original_files = {f.path: f for f in original_index.index["files"]}
    loaded_files = {f.path: f for f in loaded_index.index["files"]}
    
    assert set(original_files.keys()) == set(loaded_files.keys())
    
    for path in original_files:
        assert original_files[path].type == loaded_files[path].type
        assert original_files[path].size == loaded_files[path].size


def test_search_files(temp_repo):
    """Test file searching."""
    indexer = FileIndexer(temp_repo)
    index = indexer.create_index()
    
    # Test case-insensitive search
    results = index.search_files("main", case_sensitive=False)
    assert len(results) == 1
    assert results[0].path == "src/main.py"
    
    # Test case-sensitive search
    results = index.search_files("MAIN", case_sensitive=True)
    assert len(results) == 0
    
    # Test partial match
    results = index.search_files("py", case_sensitive=False)
    assert len(results) == 2
    assert all(f.path.endswith(".py") for f in results)


def test_get_files_by_type(temp_repo):
    """Test getting files by type."""
    indexer = FileIndexer(temp_repo)
    index = indexer.create_index()
    
    python_files = index.get_files_by_type(FileType.PYTHON)
    assert len(python_files) == 2
    assert all(f.type == FileType.PYTHON for f in python_files)
    
    js_files = index.get_files_by_type(FileType.JAVASCRIPT)
    assert len(js_files) == 1
    assert js_files[0].path == "js/app.js"