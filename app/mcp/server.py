from app.mcp.instance import mcp  # ← import, don't recreate

# Import tools so their @mcp.tool decorators run on import and register with the server.
import app.mcp.tools.products  # noqa: F401
import app.mcp.tools.customers  # noqa: F401
import app.mcp.tools.sales  # noqa: F401


if __name__ == "__main__":
    mcp.run()