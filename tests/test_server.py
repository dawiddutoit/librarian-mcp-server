"""Tests for the MCP server functionality."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from mcp.server import Server
from mcp.server.models import InitializationOptions

from librarian_mcp_server.models import FileType
from librarian_mcp_server.server import LibrarianServer


@pytest.fixture
def mock_indexer():
    """Create a mock indexer with test data."""
    from librarian_mcp_server.models import FileEntry, RepositoryInfo, WorkspaceIndex
    from datetime import datetime
    
    # Create test file entries
    test_files = [
        FileEntry(
            path="src/main.py",
            type=FileType.PYTHON,
            size=1024,
            modified=datetime.now(),
            hash="abc123"
        ),
        FileEntry(
            path="src/utils.py",
            type=FileType.PYTHON,
            size=512,
            modified=datetime.now(),
            hash="def456"
        ),
        FileEntry(
            path="frontend/app.js",
            type=FileType.JAVASCRIPT,
            size=2048,
            modified=datetime.now(),
            hash="ghi789"
        ),
        FileEntry(
            path="frontend/App.tsx",
            type=FileType.TYPESCRIPT,
            size=3072,
            modified=datetime.now(),
            hash="jkl012"
        ),
    ]
    
    # Create test index
    test_index = WorkspaceIndex(
        last_updated=datetime.now(),
        repository=RepositoryInfo(
            path="/test/repo",
            total_files=4
        )
    )
    
    for file_entry in test_files:
        test_index.add_file(file_entry)
    
    # Create mock indexer
    mock_indexer = Mock()
    mock_indexer.repo_path = Path("/test/repo")
    mock_indexer.index_path = Path("/test/repo/.claude/workspace/workspace.yml")
    mock_indexer.get_or_create_index.return_value = test_index
    mock_indexer.refresh_index.return_value = test_index
    mock_indexer.save_index = Mock()
    
    return mock_indexer


@pytest.fixture
def librarian_server(mock_indexer):
    """Create a LibrarianServer instance with mocked indexer."""
    with patch('librarian_mcp_server.server.FileIndexer', return_value=mock_indexer):
        server = LibrarianServer()
        server.index = mock_indexer.get_or_create_index()
        return server


@pytest.mark.asyncio
async def test_search_files_tool(librarian_server):
    """Test the search_files tool."""
    # Get the tool
    tools = librarian_server.server.get_tools()
    search_tool = next(t for t in tools if t.name == "search_files")
    
    # Test case-insensitive search
    result = await search_tool.fn(query="main", case_sensitive=False, limit=10)
    assert "Found 1 file(s) matching 'main'" in result
    assert "src/main.py" in result
    
    # Test case-sensitive search
    result = await search_tool.fn(query="APP", case_sensitive=True)
    assert "Found 1 file(s) matching 'APP'" in result
    assert "frontend/App.tsx" in result
    
    # Test no results
    result = await search_tool.fn(query="nonexistent", case_sensitive=False)
    assert "No files found" in result


@pytest.mark.asyncio
async def test_search_files_regex_tool(librarian_server):
    """Test the search_files_regex tool."""
    tools = librarian_server.server.get_tools()
    regex_tool = next(t for t in tools if t.name == "search_files_regex")
    
    # Test valid regex
    result = await regex_tool.fn(pattern=r".*\.py$", case_sensitive=False)
    assert "Found 2 file(s) matching regex" in result
    assert "src/main.py" in result
    assert "src/utils.py" in result
    
    # Test invalid regex
    result = await regex_tool.fn(pattern=r"[invalid", case_sensitive=False)
    assert "Invalid regex pattern" in result


@pytest.mark.asyncio
async def test_search_by_type_tool(librarian_server):
    """Test the search_by_type tool."""
    tools = librarian_server.server.get_tools()
    type_tool = next(t for t in tools if t.name == "search_by_type")
    
    # Test Python files
    result = await type_tool.fn(file_type="python", pattern=None, limit=10)
    assert "Found 2 python file(s)" in result
    assert "src/main.py" in result
    assert "src/utils.py" in result
    
    # Test with pattern filter
    result = await type_tool.fn(file_type="python", pattern="main", limit=10)
    assert "Found 1 python file(s)" in result
    assert "src/main.py" in result
    
    # Test invalid file type
    result = await type_tool.fn(file_type="invalid_type", pattern=None, limit=10)
    assert "Invalid file type" in result


@pytest.mark.asyncio
async def test_refresh_index_tool(librarian_server, mock_indexer):
    """Test the refresh_index tool."""
    tools = librarian_server.server.get_tools()
    refresh_tool = next(t for t in tools if t.name == "refresh_index")
    
    result = await refresh_tool.fn()
    
    assert "Index refreshed successfully" in result
    assert "Repository: /test/repo" in result
    assert "Total files: 4" in result
    mock_indexer.refresh_index.assert_called_once()
    mock_indexer.save_index.assert_called_once()


@pytest.mark.asyncio
async def test_get_index_stats_tool(librarian_server):
    """Test the get_index_stats tool."""
    tools = librarian_server.server.get_tools()
    stats_tool = next(t for t in tools if t.name == "get_index_stats")
    
    result = await stats_tool.fn()
    
    assert "Index Statistics:" in result
    assert "Repository: /test/repo" in result
    assert "Total files: 4" in result
    assert "python: 2" in result
    assert "javascript: 1" in result
    assert "typescript: 1" in result


@pytest.mark.asyncio
async def test_index_stats_resource(librarian_server):
    """Test the index://stats resource."""
    resources = librarian_server.server.get_resources()
    stats_resource = next(r for r in resources if r.uri == "index://stats")
    
    result = await stats_resource.fn()
    stats = json.loads(result)
    
    assert stats["total_files"] == 4
    assert stats["file_types"]["python"] == 2
    assert stats["file_types"]["javascript"] == 1
    assert stats["file_types"]["typescript"] == 1


@pytest.mark.asyncio
async def test_index_config_resource(librarian_server):
    """Test the index://config resource."""
    resources = librarian_server.server.get_resources()
    config_resource = next(r for r in resources if r.uri == "index://config")
    
    result = await config_resource.fn()
    config = json.loads(result)
    
    assert config["repository_path"] == "/test/repo"
    assert config["version"] == "0.1.0"
    assert "python" in config["supported_file_types"]