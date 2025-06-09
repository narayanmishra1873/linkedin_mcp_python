from fastmcp import FastMCP
from tools.health_check import health_check
from tools.scrape_linkedin_post import scrape_linkedin_post
from tools.extract_linkedin_profile_data import extract_linkedin_profile_data
from tools.extract_company_employees import extract_company_employees
from tools.send_connection_request import send_connection_request
from tools.generate_linkedin_content import generate_linkedin_content
import logging
from dotenv import load_dotenv

# Configure logging to show in Render logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()

mcp = FastMCP("LinkedInCommentsScraper", stateless_http=True)

# Register tools programmatically
mcp.add_tool(health_check, description="Health check tool to verify MCP server is running properly.")
mcp.add_tool(scrape_linkedin_post, description="Scrape comments from a LinkedIn post URL. Requires LinkedIn credentials.")
mcp.add_tool(extract_linkedin_profile_data, description="Extract profile data from a LinkedIn profile URL.")
mcp.add_tool(extract_company_employees, description="Extract employee information from a company using either company name or LinkedIn company URL. Prioritizes high-designation employees.")
mcp.add_tool(send_connection_request, description="Send a connection request to a LinkedIn profile URL. (Optional: include a personalized message of at max 180 characters. If the user has not provided any message, but wants to send a personalized invite, use extract_linkedin_profile_data tool to get the profile data and use it to create a personalized message.)")
mcp.add_tool(generate_linkedin_content, description="Generate engaging LinkedIn posts by analyzing existing posts on a topic. Searches LinkedIn posts via Google(default 10 unless mentioned otherwise), extracts content, and uses AI to create viral, thought-provoking posts for industry leaders. Show the generated output to the user as it is.")

if __name__ == "__main__":
    # For production hosting on Render - use streamable-http transport
    # Get port from environment variable (Render sets PORT)
    #port = int(os.environ.get("PORT", 8000))
    # Run with streamable-http transport binding to 0.0.0.0 for external access
    '''mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
        log_level="debug",
    )'''
    # For local development, use the default transport
    mcp.run()
