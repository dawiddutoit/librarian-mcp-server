"""Entry point for the Librarian MCP Server."""

import asyncio
import sys

from .server import LibrarianServer


def main():
    """Main entry point."""
    try:
        server = LibrarianServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nShutting down Librarian MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()