from fastmcp import FastMCP
from playwright.async_api import async_playwright
import asyncio
import re
import os
import logging
from dotenv import load_dotenv
import pandas as pd
import json
from google import genai

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
            browser = await p.chromium.launch(headless=False)
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

@mcp.tool()
async def extract_linkedin_profile_data(
    profile_url: str,
    username: str = None,
    password: str = None
) -> str:
    """
    Extracts comprehensive profile data from a LinkedIn profile URL using AI.
    
    Args:
        profile_url: The LinkedIn profile URL to extract data from
        username: LinkedIn username/email (optional, falls back to env var)
        password: LinkedIn password (optional, falls back to env var)
    
    Returns:
        CSV formatted string with extracted profile data including name, headline, 
        location, about, experience, education, skills, certifications, and languages
    """
    # Use provided credentials or fall back to environment variables
    linkedin_username = username or os.getenv("LINKEDIN_USERNAME")
    linkedin_password = password or os.getenv("LINKEDIN_PASSWORD")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not linkedin_username or not linkedin_password:
        return "Missing LinkedIn credentials. Please provide username and password parameters or set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables."
    
    if not google_api_key:
        return "Missing Google API key. Please set GOOGLE_API_KEY environment variable."
    
    logger.info(f"Starting LinkedIn profile data extraction")
    logger.info(f"Target profile URL: {profile_url}")
    
    async with async_playwright() as p:
        try:
            logger.info("Launching Playwright browser...")
            browser = await p.chromium.launch(headless=False)
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
            
            # Navigate to the target profile URL
            logger.info(f"Navigating to profile: {profile_url}")
            await page.goto(profile_url)
            await page.wait_for_load_state()
            await asyncio.sleep(3)
            logger.info("Profile page loaded, extracting content...")
            
            # Extract all body text content
            try:
                page_text = await page.locator('body').text_content()
                logger.info("Successfully extracted page content")
            except Exception as e:
                logger.error(f"Error extracting page content: {e}")
                await browser.close()
                return f"Error extracting page content: {str(e)}"
            
            await browser.close()
            
            # Clean the extracted text
            logger.info("Cleaning extracted text...")
            cleaned_text = _clean_profile_text(page_text)
            
            # Extract data using Gemini AI
            logger.info("Processing text with Gemini AI...")
            profile_data = await _extract_data_with_gemini(cleaned_text, google_api_key)
            
            if profile_data:
                # Convert to CSV format
                df = pd.DataFrame([profile_data])
                csv_data = df.to_csv(index=False)
                logger.info("Successfully extracted and formatted profile data")
                return csv_data
            else:
                return "Failed to extract profile data using AI."
                
        except Exception as e:
            if 'browser' in locals():
                await browser.close()
            logger.error(f"Error in profile extraction: {str(e)}")
            return f"Error: {str(e)}"

def _clean_profile_text(raw_text: str) -> str:
    """Clean the extracted profile text by removing irrelevant content."""
    if not raw_text:
        return ""
    
    lines = raw_text.split('\n')
    cleaned_lines = []
    skip_to_search_found = False
    
    for line in lines:
        if not skip_to_search_found:
            if 'Skip to search' in line:
                skip_to_search_found = True
            continue  # Skip lines until 'Skip to search' is found
        
        # Remove dictionary-like text blocks
        cleaned_line = re.sub(r'\{.*?\}\s*', '', line, flags=re.DOTALL)
        
        # Keep the line if it's not empty after stripping whitespace
        if cleaned_line.strip():
            cleaned_lines.append(cleaned_line.strip())
        
        # Stop at InterestsInterests section
        if 'InterestsInterests' in cleaned_line:
            break
    
    return "\n".join(cleaned_lines)

async def _extract_data_with_gemini(content: str, api_key: str) -> dict:
    """Extract structured profile data using Gemini AI."""
    try:
        llm = genai.Client(api_key=api_key)
        model = "gemini-2.0-flash"
        
        prompt = f"""
You are an expert LinkedIn profile data extraction specialist with deep understanding of professional profile structures and date formats. Your task is to meticulously extract structured information from the LinkedIn profile text below and return a perfectly formatted JSON object.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no explanations, comments, or additional text
2. Use double quotes for all JSON keys and string values
3. Handle missing information gracefully with appropriate defaults
4. Pay special attention to date extraction and formatting
5. Preserve all professional details accurately

EXTRACTION GUIDELINES:

**DATE FORMATS TO RECOGNIZE:**
- Full dates: "January 2020", "Jan 2020", "2020-01", "01/2020"
- Year only: "2020", "2021"
- Present/Current: "Present", "Current", "Now", "Ongoing"
- Partial dates: "Q1 2020", "Spring 2021", "Summer 2022"
- Duration formats: "2 years 3 months", "6 months"

**EXPERIENCE EXTRACTION:**
- Extract ALL work experiences, internships, volunteer work, and freelance projects
- For each experience, capture: job title, company name, employment type (if mentioned), precise start/end dates, location, and comprehensive description
- Look for keywords like: "at", "with", "worked as", "employed by", "consultant for"
- Pay attention to date ranges separated by "-", "to", "through"

**EDUCATION EXTRACTION:**
- Extract ALL educational institutions, certifications, courses, and training programs
- For each education entry, capture: institution name, degree/certification type, field of study, graduation date or date range, GPA (if mentioned), honors/achievements
- Look for: universities, colleges, online courses, bootcamps, professional certifications

**SKILLS EXTRACTION:**
- Extract technical skills, soft skills, languages, tools, frameworks, methodologies
- Look in dedicated skills sections and also mentioned throughout experience descriptions
- Include proficiency levels if mentioned

**OUTPUT FORMAT:**
Return a JSON object with these exact field names:
{{
  "Name": "string",
  "Headline": "string", 
  "Location": "string",
  "About": "string",
  "Experience": [
    {{
      "Title": "string",
      "Company": "string",
      "Employment_Type": "string",
      "Start_Date": "string",
      "End_Date": "string",
      "Duration": "string",
      "Location": "string",
      "Description": "string"
    }}
  ],
  "Education": [
    {{
      "Institution": "string",
      "Degree": "string",
      "Field_of_Study": "string",
      "Start_Date": "string",
      "End_Date": "string",
      "Grade": "string",
      "Activities": "string"
    }}
  ],
  "Skills": "comma-separated string of all skills",
  "Certifications": "comma-separated string of certifications",
  "Languages": "comma-separated string of languages"
}}

DEFAULT VALUES:
- Use empty string "" for missing text fields
- Use empty array [] for missing Experience/Education
- For dates: use "Not specified" if completely missing
- For End_Date: use "Present" if still ongoing

LINKEDIN PROFILE TEXT:
{content}
"""
        
        # Use asyncio.to_thread to run the synchronous API call
        response = await asyncio.to_thread(
            llm.models.generate_content,
            model=model,
            contents=prompt
        )
        
        raw_response = response.text.strip()
        logger.info("Received response from Gemini AI")
        
        # Clean up the response
        if raw_response.startswith("```json") or raw_response.startswith("```"):
            raw_response = raw_response.replace("```json", "").replace("```", "").strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate and format the data for CSV
            validated_data = _validate_and_format_for_csv(data)
            return validated_data
        else:
            logger.error("No valid JSON found in Gemini response")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing with Gemini: {e}")
        return None

def _validate_and_format_for_csv(data: dict) -> dict:
    """Validate and format the extracted data for CSV output."""
    if not isinstance(data, dict):
        return _create_fallback_result()
    
    # Format experience for CSV
    experience_list = data.get('Experience', [])
    if isinstance(experience_list, list) and experience_list:
        formatted_experiences = []
        for exp in experience_list:
            if isinstance(exp, dict):
                title = exp.get('Title', '')
                company = exp.get('Company', '')
                start_date = exp.get('Start_Date', '')
                end_date = exp.get('End_Date', '')
                
                exp_str = f"{title} at {company}"
                if start_date or end_date:
                    exp_str += f" ({start_date} - {end_date})"
                formatted_experiences.append(exp_str)
        experience_str = "; ".join(formatted_experiences)
    else:
        experience_str = ""
    
    # Format education for CSV
    education_list = data.get('Education', [])
    if isinstance(education_list, list) and education_list:
        formatted_education = []
        for edu in education_list:
            if isinstance(edu, dict):
                degree = edu.get('Degree', '')
                institution = edu.get('Institution', '')
                field = edu.get('Field_of_Study', '')
                start_date = edu.get('Start_Date', '')
                end_date = edu.get('End_Date', '')
                
                edu_str = f"{degree} at {institution}"
                if field:
                    edu_str += f" ({field})"
                if start_date or end_date:
                    edu_str += f" [{start_date} - {end_date}]"
                formatted_education.append(edu_str)
        education_str = "; ".join(formatted_education)
    else:
        education_str = ""
    
    return {
        'Name': data.get('Name', ''),
        'Headline': data.get('Headline', ''),
        'Location': data.get('Location', ''),
        'About': data.get('About', ''),
        'Experience': experience_str,
        'Education': education_str,
        'Skills': data.get('Skills', ''),
        'Certifications': data.get('Certifications', ''),
        'Languages': data.get('Languages', '')
    }

def _create_fallback_result() -> dict:
    """Create a fallback result when extraction fails."""
    return {
        'Name': '',
        'Headline': '',
        'Location': '',
        'About': '',
        'Experience': '',
        'Education': '',
        'Skills': '',
        'Certifications': '',
        'Languages': ''
    }

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
