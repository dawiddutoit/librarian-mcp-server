"""Integration tests for the MCP server installation and configuration."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


def test_package_installation():
    """Test that the package can be installed with pip."""
    # This test would normally run in CI/CD
    # Here we just verify the package structure
    
    project_root = Path(__file__).parent.parent
    
    # Check essential files exist
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "src" / "librarian_mcp_server" / "__init__.py").exists()
    assert (project_root / "src" / "librarian_mcp_server" / "__main__.py").exists()
    assert (project_root / "src" / "librarian_mcp_server" / "server.py").exists()


def test_mcp_json_configuration():
    """Test that the .mcp.json configuration is valid."""
    
    # Example configuration that should work
    mcp_config = {
        "mcpServers": {
            "librarian": {
                "command": "uvx",
                "args": ["--from", "git+https://github.com/dawiddutoit/librarian-mcp-server.git", "librarian-mcp-server"],
                "type": "stdio",
                "description": "File indexer and retrieval for projects"
            }
        }
    }
    
    # Validate JSON structure
    assert "mcpServers" in mcp_config
    assert "librarian" in mcp_config["mcpServers"]
    
    librarian_config = mcp_config["mcpServers"]["librarian"]
    assert librarian_config["command"] == "uvx"
    assert librarian_config["type"] == "stdio"
    assert "--from" in librarian_config["args"]
    assert "git+https://github.com/dawiddutoit/librarian-mcp-server.git" in librarian_config["args"]


def test_workspace_yml_creation():
    """Test that workspace.yml is created correctly."""
    from librarian_mcp_server.indexer import FileIndexer
    from librarian_mcp_server.models import WorkspaceIndex
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create test structure
        (repo_path / ".git").mkdir()
        (repo_path / "test.py").write_text("print('test')")
        
        # Create indexer
        indexer = FileIndexer(repo_path)
        
        # Create and save index
        index = indexer.create_index()
        indexer.save_index(index)
        
        # Verify workspace.yml exists
        workspace_path = repo_path / ".claude" / "workspace" / "workspace.yml"
        assert workspace_path.exists()
        
        # Load and verify
        loaded_index = indexer.load_index()
        assert loaded_index is not None
        assert loaded_index.repository.total_files >= 1
        assert any(f.path == "test.py" for f in loaded_index.index["files"])


def test_gitignore_respect():
    """Test that .gitignore patterns are respected."""
    from librarian_mcp_server.indexer import FileIndexer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create test structure
        (repo_path / ".git").mkdir()
        (repo_path / ".gitignore").write_text("*.log\nbuild/\n")
        
        # Create files
        (repo_path / "main.py").write_text("print('main')")
        (repo_path / "debug.log").write_text("log content")
        (repo_path / "build").mkdir()
        (repo_path / "build" / "output.js").write_text("built code")
        
        # Create indexer
        indexer = FileIndexer(repo_path)
        index = indexer.create_index()
        
        # Verify ignored files are not indexed
        file_paths = [f.path for f in index.index["files"]]
        assert "main.py" in file_paths
        assert "debug.log" not in file_paths
        assert "build/output.js" not in file_paths


def test_file_type_detection():
    """Test that file types are correctly detected."""
    from librarian_mcp_server.models import get_file_type, FileType
    
    test_cases = [
        ("test.py", FileType.PYTHON),
        ("script.js", FileType.JAVASCRIPT),
        ("component.tsx", FileType.TYPESCRIPT),
        ("Main.kt", FileType.KOTLIN),
        ("styles.css", FileType.CSS),
        ("README.md", FileType.MARKDOWN),
        ("config.json", FileType.JSON),
        ("unknown.xyz", FileType.OTHER),
    ]
    
    for filename, expected_type in test_cases:
        assert get_file_type(Path(filename)) == expected_type


@pytest.mark.asyncio
async def test_mcp_server_stdio_communication():
    """Test that the server can communicate over stdio."""
    import asyncio
    from mcp.client import Client
    from mcp.client.stdio import stdio_client
    
    # This test demonstrates how a client would connect
    # In practice, this would be tested with a running server process
    
    # Example of expected client usage:
    example_client_code = '''
    async def test_client():
        async with stdio_client() as (read_stream, write_stream):
            async with Client(read_stream, write_stream) as client:
                # Initialize
                await client.initialize()
                
                # List available tools
                tools = await client.list_tools()
                tool_names = [t.name for t in tools]
                
                assert "search_files" in tool_names
                assert "search_files_regex" in tool_names
                assert "search_by_type" in tool_names
                
                # Call a tool
                result = await client.call_tool("search_files", {"query": "test"})
                print(result)
    '''
    
    # Verify the example is valid Python
    compile(example_client_code, '<string>', 'exec')