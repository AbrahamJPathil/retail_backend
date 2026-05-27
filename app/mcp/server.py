from fastmcp import FastMCP

mcp = FastMCP("Retail MCP")

# Import tools so their @mcp.tool decorators run on import and register with the server.
import app.mcp.tools.products  # noqa: F401
import app.mcp.tools.customers  # noqa: F401
import app.mcp.tools.sales  # noqa: F401


if __name__ == "__main__":
    # Run with stdio by default for local development. Use --transport http for remote access.
    mcp.run()
