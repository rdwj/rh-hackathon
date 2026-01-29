"""
Resources package for the MCP server.

Resource modules are automatically discovered and loaded by src/core/loaders.py.

To add a new resource:
1. Create a new .py file in this directory (subdirectories are supported)
2. Import mcp from core.app: from core.app import mcp
3. Define your resource function with @mcp.resource() decorator
4. The loader will automatically discover and import it

To remove a resource:
1. Simply delete the .py file
"""
