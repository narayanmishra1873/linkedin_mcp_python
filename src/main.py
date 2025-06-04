"""
Alternative entry point for running the LinkedIn MCP server with uvicorn directly.
This provides more control over the server configuration for cloud deployments.
"""
import os
import uvicorn
from server import mcp

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    # Run with uvicorn for better cloud compatibility
    uvicorn.run(
        mcp.app,  # FastMCP creates an internal FastAPI app
        host=host,
        port=port,
        log_level="info"
    )
