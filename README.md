# Librarian MCP Server

A high-performance MCP (Model Context Protocol) server that provides intelligent file indexing and lightning-fast search capabilities for your repositories. Librarian automatically creates and maintains an index of your project files, enabling instant file discovery without repeated filesystem traversal.

## Why Librarian?

When working with large codebases, finding files quickly is crucial. Traditional file search methods require traversing the entire filesystem each time, which can be slow. Librarian solves this by maintaining an efficient index at `.claude/workspace/workspace.yml`, providing:

- **Instant Results**: Search through thousands of files in milliseconds
- **Smart Indexing**: Automatically respects `.gitignore` patterns
- **Type-Aware**: Built-in understanding of 19+ programming languages
- **Zero Configuration**: Works out of the box with any git repository

## Features

- 🚀 **Fast File Search** - Search files by name pattern without filesystem traversal
- 🔍 **Regex Search** - Use regular expressions for advanced file searching
- 📁 **Type-based Search** - Find files by type (Python, JavaScript, TypeScript, etc.)
- 📊 **Index Statistics** - Get insights about your repository structure
- 🔄 **Index Refresh** - Update the index when files change
- 🚫 **Gitignore Support** - Automatically respects `.gitignore` patterns
- 📦 **Language Support** - Recognizes 19+ programming languages and file types
- 🔧 **MCP Protocol** - Full compliance with Model Context Protocol standards

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

## Examples

### Basic File Search
```python
# Search for files containing "user" in the name
result = await search_files("user")
# Returns: UserController.py, user_model.py, user.test.js

# Case-sensitive search
result = await search_files("README", case_sensitive=True)
# Returns: README.md (but not readme.txt)
```

### Regex Search
```python
# Find all test files
result = await search_files_regex(r".*\.test\.(js|py|ts)$")

# Find files with version numbers
result = await search_files_regex(r"v\d+\.\d+")
```

### Search by File Type
```python
# Find all Python files
result = await search_by_type("python")

# Find TypeScript files with "component" in the name
result = await search_by_type("typescript", pattern="component")
```

## How It Works

1. **Automatic Detection**: Librarian automatically detects your repository root by finding the `.git` directory
2. **Smart Indexing**: On first run, it scans your repository and creates an index, ignoring files in `.gitignore`
3. **Fast Retrieval**: All searches use the pre-built index for instant results
4. **Easy Updates**: Use the `refresh_index` tool to update the index when files change

## Supported File Types

Librarian recognizes and categorizes files by type:

- **Python**: `.py`, `.pyi`, `.pyx`, `.pxd`
- **JavaScript**: `.js`, `.mjs`, `.cjs`
- **TypeScript**: `.ts`, `.tsx`, `.d.ts`
- **Java**: `.java`
- **Kotlin**: `.kt`, `.kts`
- **Go**: `.go`
- **Rust**: `.rs`
- **C/C++**: `.c`, `.h`, `.cpp`, `.hpp`, `.cc`
- **C#**: `.cs`
- **Ruby**: `.rb`
- **PHP**: `.php`
- **Swift**: `.swift`
- **Web**: `.html`, `.css`, `.scss`
- **Data**: `.json`, `.yaml`, `.xml`
- **Documentation**: `.md`, `.markdown`

## Performance

Librarian is designed for speed:
- Initial indexing: ~1000 files/second
- Search operations: <10ms for repos with 10,000+ files
- Memory efficient: Index size is typically <1% of repository size

## Development

### Prerequisites
- Python 3.10+
- UV package manager

### Setup
```bash
# Clone the repository
git clone https://github.com/dawiddutoit/librarian-mcp-server.git
cd librarian-mcp-server

# Install dependencies with UV
uv pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=librarian_mcp_server

# Run specific test file
pytest tests/test_integration.py
```

### Building
```bash
# Build distribution packages
uv build

# The built packages will be in dist/
ls dist/
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Index not updating?
Run the `refresh_index` tool to manually update the index:
```json
{"tool": "refresh_index"}
```

### Files missing from search?
Check if they're ignored by `.gitignore`. Librarian respects gitignore patterns.

### Performance issues?
For very large repositories (>50,000 files), the initial indexing might take a few seconds. Subsequent searches remain fast.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with the [Model Context Protocol](https://modelcontextprotocol.io) to provide seamless integration with AI assistants.