import os
import logging
import asyncio
from playwright.async_api import async_playwright
from .linkedin_login import ensure_linkedin_login, STORAGE_STATE_PATH

async def send_connection_request(
    profile_url: str,
    message: str = None,
    username: str = None,
    password: str = None
) -> str:
    """
    Send a connection request to a LinkedIn user.
    
    Args:
        profile_url: LinkedIn profile URL (e.g., "https://www.linkedin.com/in/username/")
        message: Optional connection request message (max 180 characters)
        username: LinkedIn username/email (optional, falls back to env var)
        password: LinkedIn password (optional, falls back to env var)
    
    Returns:
        String indicating success or failure of the connection request
    """
    linkedin_username = username or os.getenv("LINKEDIN_USERNAME")
    linkedin_password = password or os.getenv("LINKEDIN_PASSWORD")
    logger = logging.getLogger(__name__)
    
    if not linkedin_username or not linkedin_password:
        return "Missing LinkedIn credentials. Please provide username and password parameters or set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables."
    
    if not profile_url:
        return "Error: profile_url is required."
    
    # Validate profile URL
    if not profile_url.startswith("https://www.linkedin.com/in/"):
        return "Error: Invalid LinkedIn profile URL. URL should start with 'https://www.linkedin.com/in/'"
    
    # Validate message length if provided
    if message and len(message) > 200:  # For safety
        return f"Error: Message too long ({len(message)} characters). Maximum allowed is 200 characters."

    logger.info(f"Starting connection request to profile: {profile_url}")
    if message:
        logger.info(f"With message: {message}")
    
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
            
            # Navigate to the profile URL
            logger.info(f"Navigating to profile: {profile_url}")
            await page.goto(profile_url)
            await asyncio.sleep(3)
            
            # Wait for page to load
            await page.wait_for_load_state('load', timeout=0)

            # --- START OF INTEGRATED SEND CONNECTION LOGIC ---

            # 1. Check for "Pending" or "Withdraw" (already sent request)
            pending_button = await page.query_selector('main button:has-text("Pending"), main button:has-text("Withdraw")')
            if pending_button:
                logger.info("Connection request already pending. Skipping...")
                await browser.close()
                return "Connection request already pending. Skipping..."

            # 2. Check for "Message" button with icon (already connected)
            more_button = await page.wait_for_selector('main button:has-text("More")', timeout=10000)

            # Get the parent container of the 'More' button (typically the div holding all main action buttons)
            grandparent = await more_button.evaluate_handle('el => el.parentElement.parentElement')

            # Count the number of buttons inside this grandparent container
            main_action_buttons_count = await grandparent.evaluate('el => el.querySelectorAll("button").length')

            if main_action_buttons_count == 2:
                await browser.close()
                return "Already connected. Skipping..."

            # 3. Check for "Connect" or "More" (not connected)
            connect_button = await page.query_selector('main button:has-text("Connect")')
            if connect_button:
                await connect_button.click()
            else:
                # If not found, click "More"
                more_button = await page.query_selector('main button:has-text("More")')
                if more_button:
                    await more_button.click()
                    # Wait for dropdown to appear
                    await asyncio.sleep(1)
                    await page.evaluate("window.scrollBy(0, 200)")
                    # Wait for the dropdown item to be visible
                    await page.wait_for_selector('div.artdeco-dropdown__content--is-open', timeout=10000)

                    # Now locate and click the "Connect" option inside the open dropdown
                    connect_option = page.locator('div.artdeco-dropdown__content--is-open [role="button"] span:has-text("Connect")').first
                    if await connect_option.count() > 0:
                        await connect_option.click()
                    else:
                        logger.info("Connect button not found in More menu.")
                        await browser.close()
                        return "Connect button not found in More menu."
                else:
                    logger.info("Neither Connect nor More button found on main profile.")
                    await browser.close()
                    return "Neither Connect nor More button found on main profile."

            # Handle connection popup
            if message:
                # Wait for the "Add a note" button to be visible
                await asyncio.sleep(1)
                add_note_button = page.locator('button[aria-label="Add a note"]')
                if await add_note_button.count() > 0:
                    await add_note_button.click()
                    # Wait for the invitation textarea to be visible
                    await page.wait_for_selector('textarea[name="message"]', timeout=10000)
                    # Fill the textarea with your message
                    await page.fill('textarea[name="message"]', message)
                    # Wait for the "Send invitation" button to be visible and click it
                    send_button = page.locator('button[aria-label="Send invitation"]')
                    await send_button.click()
                else:
                    logger.info("Add a note button not found. Sending without a note.")
                    # Fallback to send without a note
                    send_button = page.locator('button[aria-label="Send without a note"]')
                    await send_button.click()
            else:
                # Wait for the "Send without a note" button to be visible
                send_button = page.locator('button[aria-label="Send without a note"]')
                await send_button.click()

            # Wait for request to be processed
            await asyncio.sleep(3)

            await browser.close()
            
            return f"✅ Connection request sent successfully to {profile_url} with message: '{message}'"
                
            # --- END OF INTEGRATED SEND CONNECTION LOGIC ---

        except Exception as e:
            if 'browser' in locals():
                try:
                    await browser.close()
                except:
                    pass
            logger.error(f"Error sending connection request: {str(e)}")
            return f"Error: {str(e)}"
