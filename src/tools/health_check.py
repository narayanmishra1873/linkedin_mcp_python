async def health_check() -> str:
    """
    Simple health check tool to verify the MCP server is running properly.
    Returns:
        A simple status message confirming the server is operational.
    """
    return "LinkedIn Comments Scraper MCP Server is healthy and ready to scrape!"
