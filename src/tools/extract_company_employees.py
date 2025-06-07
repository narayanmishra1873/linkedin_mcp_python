# filepath: d:\CashRich\2025\LinkedIN\comments\comments_mcp\linkedin_mcp_python\src\tools\extract_company_employees.py
import os
import logging
import pandas as pd
import re
import asyncio
from playwright.async_api import async_playwright
from .linkedin_login import ensure_linkedin_login, STORAGE_STATE_PATH
from urllib.parse import quote_plus

# High-designation keywords to prioritize in search results
HIGH_DESIGNATION_KEYWORDS = [
    'CEO', 'CTO', 'CFO', 'COO', 'President', 'Vice President', 'VP', 'SVP',
    'Director', 'Senior Director', 'Executive Director', 'Managing Director',
    'Head of', 'Lead', 'Senior Manager', 'Manager', 'Principal', 'Senior',
    'Founder', 'Co-Founder', 'Partner', 'Senior Partner', 'Associate Director',
    'Chief', 'Senior Vice President', 'Executive Vice President', 'EVP', 'Founder'
]


async def _navigate_to_people_page(page, company_name: str = None, company_url: str = None) -> str:
    """
    Navigates to the LinkedIn company people page given a company name or company URL.
    Returns the final people page URL or None if not found.
    """
    logger = logging.getLogger(__name__)
    
    # Route 1: Direct company people URL provided
    if company_url and '/people' in company_url:
        logger.info(f"Direct people URL provided: {company_url}")
        await page.goto(company_url)
        await asyncio.sleep(3)
        logger.info("Successfully navigated to people page")
        return company_url
    
    # Route 2: Company URL provided (but not people page) - go to company page then click People tab
    elif company_url and '/company/' in company_url:
        logger.info(f"Company URL provided: {company_url}")
        await page.goto(company_url)
        await asyncio.sleep(3)
        
        try:
            # Look for People tab and click it
            people_tab_selectors = [
                'a[data-control-name="people"]',
                'a[href$="/people/"]',
                'a:has-text("People")',
                'nav a[href*="/people"]'
            ]
            
            people_tab = None
            for selector in people_tab_selectors:
                people_tab = await page.query_selector(selector)
                if people_tab:
                    logger.info(f"Found People tab with selector: {selector}")
                    break
            
            if people_tab:
                await people_tab.click()
                await asyncio.sleep(3)
                logger.info("Successfully clicked People tab")
                return page.url
            else:
                logger.warning("Could not find People tab on company page")
                return None
                
        except Exception as e:
            logger.warning(f"Error clicking People tab: {str(e)}")
            return None
    
    # Route 3: Company name provided - search for company, click first result, then People tab
    elif company_name:
        logger.info(f"Company name provided: {company_name}")
        
        # Step 1: Go to companies search page
        search_url = "https://www.linkedin.com/search/results/companies/"
        logger.info(f"Navigating to companies search: {search_url}")
        await page.goto(search_url)
        await asyncio.sleep(3)
        
        try:
            # Step 2: Find search input and enter company name
            search_input_selectors = [
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
                '.search-global-typeahead__input',
                'input[data-test-id="search-input"]'
            ]
            
            search_input = None
            for selector in search_input_selectors:
                search_input = await page.query_selector(selector)
                if search_input:
                    logger.info(f"Found search input with selector: {selector}")
                    break
            
            if not search_input:
                logger.error("Could not find search input field")
                return None
            
            # Clear and type company name
            await search_input.fill(company_name)
            logger.info(f"Entered company name: {company_name}")
            
            # Press Enter or click search button
            await page.keyboard.press('Enter')
            await asyncio.sleep(3)
            logger.info("Submitted search query")
              # Step 3: Wait for results to load and click first company result
            await page.wait_for_selector('a[href*="/company/"]', timeout=10000)
            
            # Look for first company result with updated selectors
            company_result_selectors = [
                'a[data-test-app-aware-link][href*="/company/"]',
                'a.PxxmMLACwEGNeKyVHxYCskDzzJAEcLVgZk[href*="/company/"]',
                'a[href*="/company/"]',
                '.entity-result a[href*="/company/"]',
                '.search-result a[href*="/company/"]'
            ]
            
            first_company = None
            for selector in company_result_selectors:
                first_company = await page.query_selector(selector)
                if first_company:
                    logger.info(f"Found first company result with selector: {selector}")
                    break
            
            if not first_company:
                logger.error("Could not find any company results")
                return None
            
            # Step 4: Click on first company result
            await first_company.click()
            await asyncio.sleep(3)
            logger.info("Clicked on first company result")
            
            # Step 5: Wait for company page to load and click People tab
            try:
                people_tab_selectors = [
                    'a[data-control-name="people"]',
                    'a[href$="/people/"]',
                    'a:has-text("People")',
                    'nav a[href*="/people"]'
                ]
                
                people_tab = None
                for selector in people_tab_selectors:
                    people_tab = await page.query_selector(selector)
                    if people_tab:
                        logger.info(f"Found People tab with selector: {selector}")
                        break
                
                if people_tab:
                    await people_tab.click()
                    await asyncio.sleep(3)
                    logger.info("Successfully clicked People tab")
                    return page.url
                else:
                    logger.warning("Could not find People tab on company page")
                    return None
                    
            except Exception as e:
                logger.warning(f"Error clicking People tab: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error during company search and navigation: {str(e)}")
            return None
    
    logger.error("No valid company_name or company_url provided")
    return None

async def extract_company_employees(
    company_name: str = None,
    company_url: str = None,
    max_employees: int = 30,
    username: str = None,
    password: str = None
) -> str:
    """
    Navigate to LinkedIn company people page using either company name or company URL.
    Args:
        company_name: Name of the company (e.g., "CashRich")
        company_url: LinkedIn company URL (e.g., "https://www.linkedin.com/company/cr-fintech/people/", "https://www.linkedin.com/company/cr-fintech/")
        max_employees: Maximum number of employees to extract (default: 30)
        username: LinkedIn username/email (optional, falls back to env var)
        password: LinkedIn password (optional, falls back to env var)
    
    Returns:
        CSV formatted string with employee data including name, headline, profile_url, and designation_score
    """
    linkedin_username = username or os.getenv("LINKEDIN_USERNAME")
    linkedin_password = password or os.getenv("LINKEDIN_PASSWORD")
    logger = logging.getLogger(__name__)
    
    if not linkedin_username or not linkedin_password:
        return "Missing LinkedIn credentials. Please provide username and password parameters or set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables."
    
    # Validate input parameters
    if not company_name and not company_url:
        return "Error: Either company_name or company_url must be provided."
    
    logger.info(f"Starting navigation to company people page")
    logger.info(f"Company name: {company_name}")
    logger.info(f"Company URL: {company_url}")
    
    async with async_playwright() as p:
        try:
            logger.info("Launching Playwright browser...")
            context_args = {}
            if os.path.exists(STORAGE_STATE_PATH):
                context_args['storage_state'] = STORAGE_STATE_PATH
            
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(**context_args)
            page = await context.new_page()
            
            # Login to LinkedIn
            logged_in = await ensure_linkedin_login(page, linkedin_username, linkedin_password)
            if not logged_in:
                await browser.close()
                return "Login failed or took too long."
            
            # Navigate to people page
            people_page_url = await _navigate_to_people_page(page, company_name, company_url)
            
            if people_page_url:
                logger.info(f"Successfully navigated to people page: {people_page_url}")                
                employees = []
                seen_urls = set()
                attempts = 0
                last_count = 0
                max_attempts = 30
                current_scroll_position = 0
                
                while len(employees) < max_employees and attempts < max_attempts:
                    attempts += 1
                    # Get current scroll position and new scroll height
                    current_scroll_position = await page.evaluate('() => window.pageYOffset')
                    scroll_height = await page.evaluate('() => document.body.scrollHeight')
                    
                    # Only scroll from current position to new height
                    if current_scroll_position < scroll_height:
                        for y in range(current_scroll_position, scroll_height, 500):
                            await page.evaluate(f'window.scrollTo(0, {y})')
                            await asyncio.sleep(1)

                    profiles = []
                    
                    # Wait for profile cards to be visible
                    try:
                        # Get profile cards from LinkedIn people page
                        profile_cards = await page.locator('.org-people-profile-card__profile-info').element_handles()
                        logger.info(f"Found {len(profile_cards)} profile cards")
                        
                        # Extract data from each profile card
                        for i, card in enumerate(profile_cards):
                            try:
                                # Extract profile URL from the title link
                                profile_link = await card.query_selector('.artdeco-entity-lockup__title a')
                                if profile_link:
                                    profile_url = await profile_link.get_attribute('href')
                                    # Clean the URL (remove miniProfileUrn parameter)
                                    if profile_url and '?' in profile_url:
                                        profile_url = profile_url.split('?')[0]
                                else:
                                    profile_url = None
                                
                                # Skip if we've already seen this profile URL
                                if profile_url and profile_url in seen_urls:
                                    continue
                                
                                if profile_url:
                                    seen_urls.add(profile_url)
                                
                                # Extract name from the title link
                                name_element = await card.query_selector('.artdeco-entity-lockup__title a .lt-line-clamp')
                                name = await name_element.inner_text() if name_element else "N/A"
                                name = name.strip()
                                
                                # Extract headline from subtitle
                                headline_element = await card.query_selector('.artdeco-entity-lockup__subtitle .lt-line-clamp')
                                headline = await headline_element.inner_text() if headline_element else "N/A"
                                headline = headline.strip()
                                
                                
                                # Add to employees list if we have valid data
                                if name and name != "N/A" and name != "LinkedIn Member":
                                    employees.append({
                                        'name': name,
                                        'headline': headline,
                                        'profile_url': profile_url or "N/A"
                                    })
                                    logger.info(f"Extracted: {name} - {headline}")
                                
                                # Stop if we've reached max employees
                                if len(employees) >= max_employees:
                                    break
                                    
                            except Exception as card_error:
                                logger.warning(f"Error extracting data from card {i+1}: {card_error}")
                                continue
                        logger.info(f"Total employees extracted so far: {len(employees)}")
                        
                    except Exception as e:
                        logger.error(f"Error finding profile cards: {str(e)}")
                        return f"Error: {str(e)}"
                      # Check if we found new employees
                    if last_count == len(employees):
                        # No new employees found, try to click 'Show more' button
                        try:
                            show_more_btn = await page.query_selector('button.scaffold-finite-scroll__load-button')
                            if show_more_btn and await show_more_btn.is_enabled():
                                # Update current scroll position before clicking
                                current_scroll_position = await page.evaluate('() => window.pageYOffset')
                                await show_more_btn.click()
                                await asyncio.sleep(2)
                                logger.info("Clicked 'Show more results' button")
                            else:
                                logger.info("No more 'Show more results' button found - breaking")
                                break
                        except Exception as e:
                            logger.info(f"No more 'Show more results' button or error: {str(e)} - breaking")
                            break
                    
                    last_count = len(employees)
                import pandas as pd
                df = pd.DataFrame(employees)
                await browser.close()
                return df.to_csv(index=False)
            else:
                await browser.close()
                return f"Failed to navigate to people page for company: {company_name or company_url}"
                
        except Exception as e:
            if 'browser' in locals():
                try:
                    await browser.close()
                except:
                    pass
            logger.error(f"Error during navigation: {str(e)}")
            return f"Error: {str(e)}"
