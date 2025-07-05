# Librarian MCP Server

A fast file indexing and searching MCP (Model Context Protocol) server for repositories. Librarian creates an index of your repository files and provides instant search capabilities through MCP tools.

## Features

- 🚀 **Fast File Search** - Search files by name pattern without filesystem traversal
- 🔍 **Regex Search** - Use regular expressions for advanced file searching
- 📁 **Type-based Search** - Find files by type (Python, JavaScript, TypeScript, etc.)
- 📊 **Index Statistics** - Get insights about your repository structure
- 🔄 **Index Refresh** - Update the index when files change
- 🚫 **Gitignore Support** - Respects `.gitignore` patterns

## Installation

### Install from GitHub (recommended)
```bash
# Using uvx (recommended)
uvx --from git+https://github.com/dawiddutoit/librarian-mcp-server.git librarian-mcp-server

# Or install with pip
pip install git+https://github.com/dawiddutoit/librarian-mcp-server.git
```

### Install for development
```bash
git clone https://github.com/dawiddutoit/librarian-mcp-server.git
cd librarian-mcp-server
uv pip install -e .
```

## Configuration

Add to your `.mcp.json` configuration file:

```json
{
  "mcpServers": {
    "librarian": {
      "command": "uvx",
      "args": ["librarian-mcp-server"],
      "type": "stdio",
      "description": "File indexer and retrieval for projects"
    }
  }
}
```

## How It Works

1. **Automatic Indexing**: On first run, Librarian scans your repository and creates an index at `.claude/workspace/workspace.yml`
2. **Fast Searching**: All searches use the index for instant results without filesystem traversal
3. **Repository Detection**: Automatically detects repository root by finding `.git` directory

## Available Tools

### search_files
Search for files by name pattern (substring match).

```
Parameters:
- query: Search pattern
- case_sensitive: Whether to perform case-sensitive search (default: false)
- limit: Maximum results to return (default: 100)
```

### search_files_regex
Search for files using regular expressions.

```
Parameters:
- pattern: Regular expression pattern
- case_sensitive: Whether to perform case-sensitive search (default: false)
- limit: Maximum results to return (default: 100)
```

### search_by_type
Search for files by programming language or file type.

```
Parameters:
- file_type: Type to search for (python, javascript, typescript, kotlin, etc.)
- pattern: Optional name pattern to filter results
- limit: Maximum results to return (default: 100)
```

Supported file types:
- `python` - .py, .pyi, .pyx, .pxd
- `javascript` - .js, .mjs, .cjs
- `typescript` - .ts, .tsx, .d.ts
- `kotlin` - .kt, .kts
- `java` - .java
- `go` - .go
- `rust` - .rs
- `cpp` - .cpp, .cxx, .cc, .hpp, .hxx, .h++
- `c` - .c, .h
- `csharp` - .cs
- `ruby` - .rb
- `php` - .php
- `swift` - .swift
- `markdown` - .md, .markdown
- `json` - .json
- `yaml` - .yml, .yaml
- `xml` - .xml
- `html` - .html, .htm
- `css` - .css, .scss, .sass, .less

### refresh_index
Refresh the file index by rescanning the repository.

### get_index_stats
Get statistics about the current file index, including file counts by type.

## Resources

### index://stats
Returns current index statistics as JSON.

### index://config
Returns server configuration including repository path and supported file types.

## Index Location

The index is stored at `.claude/workspace/workspace.yml` in your repository root. This file contains:
- File paths and metadata
- File types and sizes
- Last modification times
- SHA256 hashes for change detection

## Ignored Files

Librarian automatically ignores:
- Files and directories in `.gitignore`
- Hidden files and directories (starting with `.`)
- Common build/dependency directories: `node_modules`, `__pycache__`, `venv`, `env`, `build`, `dist`, `target`
- The `.git` and `.claude` directories

## Development

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/librarian-mcp-server.git
cd librarian-mcp-server

# Install dependencies with UV
uv pip install -e ".[dev]"
```

### Running Tests
```bash
pytest
```

### Building
```bash
uv build
```

## License

MIT License - see LICENSE file for details.