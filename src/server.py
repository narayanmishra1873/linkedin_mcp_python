from fastmcp import FastMCP
from playwright.async_api import async_playwright
import asyncio
import re
import os
import logging
from dotenv import load_dotenv
import pandas as pd

# Configure logging to show in Render logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()

mcp = FastMCP("LinkedInCommentsScraper", stateless_http=True)

@mcp.tool()
async def health_check() -> str:
    """
    Simple health check tool to verify the MCP server is running properly.
    
    Returns:
        A simple status message confirming the server is operational.
    """
    return "LinkedIn Comments Scraper MCP Server is healthy and ready to scrape!"

@mcp.tool()
async def scrape_linkedin_post(
    post_url: str, 
    n: int = 20, 
    username: str = None, 
    password: str = None
) -> str:
    """
    Scrapes LinkedIn post comments looking for email addresses.
    
    Args:
        post_url: The LinkedIn post URL to scrape
        n: Maximum number of results to return (default: 20)
        username: LinkedIn username/email (optional, falls back to env var)
        password: LinkedIn password (optional, falls back to env var)
    
    Returns:
        CSV formatted string with name, headline, profile_url, and email
    """
    # Use provided credentials or fall back to environment variables
    linkedin_username = username or os.getenv("LINKEDIN_USERNAME")
    linkedin_password = password or os.getenv("LINKEDIN_PASSWORD")
    
    if not linkedin_username or not linkedin_password:
        return "Missing LinkedIn credentials. Please provide username and password parameters or set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables."
    
    logger.info(f"Starting LinkedIn scraping for user: {linkedin_username}")
    logger.info(f"Target post URL: {post_url}")
    logger.info(f"Maximum results to return: {n}")
    
    results = []
    seen_profiles = set()
    
    async with async_playwright() as p:
        try:
            logger.info("Launching Playwright browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            logger.info("Browser launched successfully")
            
            # Navigate to login page and login
            logger.info("Navigating to LinkedIn login page...")
            await page.goto("https://www.linkedin.com/login")
            await page.wait_for_selector("#username")
            logger.info("Login page loaded, filling credentials...")
            await page.fill("#username", linkedin_username)
            await page.wait_for_selector("#password")
            await page.fill("#password", linkedin_password)
            await page.click("button[type='submit']")
            logger.info("Login form submitted, waiting for authentication...")
              # Wait for successful login
            try:
                await page.wait_for_selector("input[aria-label='Search']", timeout=30000)
                logger.info("✅ Successfully logged into LinkedIn!")
            except Exception as login_error:
                logger.error(f"❌ Login failed: {str(login_error)}")
                await browser.close()
                return "Login failed or took too long."
            
            # Navigate to the target post URL
            logger.info(f"Navigating to post: {post_url}")
            await page.goto(post_url)
            await asyncio.sleep(5)
            logger.info("Post page loaded, starting comment extraction...")
            
            load_more_clicks = 0
            max_load_more_clicks = 10
            initial_comment_count = 0
            
            while len(results) < n and load_more_clicks < max_load_more_clicks:
                # Extract all comment entities
                comment_entities = await page.query_selector_all("article.comments-comment-entity")
                current_comment_count = len(comment_entities)
                logger.info(f"Found {current_comment_count} comment entities on page")
                
                # Break if no new comments are loaded
                if current_comment_count == initial_comment_count and current_comment_count > 0:
                    logger.info("No new comments loaded, breaking loop")
                    break
                initial_comment_count = current_comment_count
                
                for entity in comment_entities:
                    name = None
                    profile_url = None
                    headline = None
                    email = ""
                    
                    # Extract profile URL
                    try:
                        profile_url_elem = await entity.query_selector("a.comments-comment-meta__description-container")
                        if profile_url_elem:
                            profile_url = await profile_url_elem.get_attribute("href")
                            profile_url = profile_url.strip() if profile_url else None
                    except Exception:
                        pass
                    
                    # Extract name
                    try:
                        name_elem = await entity.query_selector("a.comments-comment-meta__description-container h3.comments-comment-meta__description span.comments-comment-meta__description-title")
                        if name_elem:
                            name = await name_elem.inner_text()
                            name = name.strip()
                    except Exception:
                        pass
                    
                    # Extract headline
                    try:
                        headline_elem = await entity.query_selector("a.comments-comment-meta__description-container div.comments-comment-meta__description-subtitle")
                        if headline_elem:
                            headline = await headline_elem.inner_text()
                            headline = headline.strip()
                    except Exception:
                        pass
                    
                    # Extract comment content and email
                    comment_text = ""
                    try:
                        comment_elem = await entity.query_selector("span.comments-comment-item__main-content")
                        if comment_elem:
                            comment_text = await comment_elem.inner_text()
                            comment_text = comment_text.strip()
                            # Extract email using regex
                            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}', comment_text)
                            email = email_match.group(0) if email_match else ""
                    except Exception:
                        email = ""
                    
                    # Skip if no email (we only want comments with emails)
                    if not email:
                        continue
                    
                    # Avoid duplicates by profile_url
                    if profile_url and profile_url in seen_profiles:
                        continue
                    if profile_url:
                        seen_profiles.add(profile_url)
                    
                    # Skip replies (comments starting with '@')
                    if comment_text and comment_text.startswith('@'):
                        continue
                    
                    results.append({
                        "name": name,
                        "headline": headline,
                        "profile_url": profile_url,
                        "email": email
                    })
                    
                    if len(results) >= n:
                        break
                
                # Try to load more comments
                try:
                    load_more_button = page.locator("button", has_text="Load more comments")
                    if await load_more_button.count() > 0:
                        await load_more_button.click(force=True)
                        await asyncio.sleep(2)
                        load_more_clicks += 1
                    else:
                        break
                except Exception:
                    break
            
            await browser.close()
            
            if results:
                # Convert to CSV format
                df = pd.DataFrame(results)
                csv_data = df.to_csv(index=False)
                return csv_data
            else:
                return "No results found."
                
        except Exception as e:
            if 'browser' in locals():
                await browser.close()
            return f"Error: {str(e)}"

if __name__ == "__main__":
    # For production hosting on Render - use streamable-http transport
    # Get port from environment variable (Render sets PORT)
    port = int(os.environ.get("PORT", 8000))
    
    # Run with streamable-http transport binding to 0.0.0.0 for external access
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
        log_level="debug",
    )
