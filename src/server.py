from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import asyncio
import re
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

mcp = FastMCP("LinkedInCommentsScraper", stateless_http=True)

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
    
    results = []
    seen_profiles = set()
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to login page and login
            await page.goto("https://www.linkedin.com/login")
            await page.wait_for_selector("#username")
            await page.fill("#username", linkedin_username)
            await page.wait_for_selector("#password")
            await page.fill("#password", linkedin_password)
            await page.click("button[type='submit']")
            
            # Wait for successful login
            try:
                await page.wait_for_selector("input[aria-label='Search']", timeout=30000)
            except Exception:
                await browser.close()
                return "Login failed or took too long."
            
            # Navigate to the target post URL
            await page.goto(post_url)
            await asyncio.sleep(5)
            
            load_more_clicks = 0
            max_load_more_clicks = 10
            initial_comment_count = 0
            
            while len(results) < n and load_more_clicks < max_load_more_clicks:
                # Extract all comment entities
                comment_entities = await page.query_selector_all("article.comments-comment-entity")
                current_comment_count = len(comment_entities)
                
                # Break if no new comments are loaded
                if current_comment_count == initial_comment_count and current_comment_count > 0:
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
    # For hosting, you can use different transport options:
    # For development: sse transport
    # For production hosting: streamable-http
    
    # Set environment variables for FastMCP streamable-http transport
    os.environ.setdefault("HOST", "0.0.0.0")
    if "PORT" not in os.environ:
        os.environ["PORT"] = "8000"
      # For HTTP hosting (recommended for external access and required for Render):
    # FastMCP automatically uses HOST and PORT environment variables for streamable-http
    mcp.run(transport="streamable-http")
    
    # For MCP protocol (development only):
    # mcp.run(transport="sse")
