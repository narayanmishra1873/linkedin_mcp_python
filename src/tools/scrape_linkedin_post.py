import os
import logging
import pandas as pd
import re
from playwright.async_api import async_playwright
from tools.linkedin_login import ensure_linkedin_login, STORAGE_STATE_PATH
import asyncio

async def scrape_linkedin_post(
    post_url: str, 
    n: int = 20, 
    username: str = None, 
    password: str = None
) -> str:
    linkedin_username = username or os.getenv("LINKEDIN_USERNAME")
    linkedin_password = password or os.getenv("LINKEDIN_PASSWORD")
    logger = logging.getLogger(__name__)
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
            context_args = {}
            if os.path.exists(STORAGE_STATE_PATH):
                context_args['storage_state'] = STORAGE_STATE_PATH
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(**context_args)
            page = await context.new_page()
            logged_in = await ensure_linkedin_login(page, linkedin_username, linkedin_password)
            if not logged_in:
                await browser.close()
                return "Login failed or took too long."
            logger.info(f"Navigating to post: {post_url}")
            await page.goto(post_url)
            await asyncio.sleep(5)
            logger.info("Post page loaded, starting comment extraction...")
            load_more_clicks = 0
            max_load_more_clicks = 10
            initial_comment_count = 0
            while len(results) < n and load_more_clicks < max_load_more_clicks:
                comment_entities = await page.query_selector_all("article.comments-comment-entity")
                current_comment_count = len(comment_entities)
                logger.info(f"Found {current_comment_count} comment entities on page")
                if current_comment_count == initial_comment_count and current_comment_count > 0:
                    logger.info("No new comments loaded, breaking loop")
                    break
                initial_comment_count = current_comment_count
                for entity in comment_entities:
                    name = None
                    profile_url = None
                    headline = None
                    email = ""
                    try:
                        profile_url_elem = await entity.query_selector("a.comments-comment-meta__description-container")
                        if profile_url_elem:
                            profile_url = await profile_url_elem.get_attribute("href")
                            profile_url = profile_url.strip() if profile_url else None
                    except Exception:
                        pass
                    try:
                        name_elem = await entity.query_selector("a.comments-comment-meta__description-container h3.comments-comment-meta__description span.comments-comment-meta__description-title")
                        if name_elem:
                            name = await name_elem.inner_text()
                            name = name.strip()
                    except Exception:
                        pass
                    try:
                        headline_elem = await entity.query_selector("a.comments-comment-meta__description-container div.comments-comment-meta__description-subtitle")
                        if headline_elem:
                            headline = await headline_elem.inner_text()
                            headline = headline.strip()
                    except Exception:
                        pass
                    comment_text = ""
                    try:
                        comment_elem = await entity.query_selector("span.comments-comment-item__main-content")
                        if comment_elem:
                            comment_text = await comment_elem.inner_text()
                            comment_text = comment_text.strip()
                            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}', comment_text)
                            email = email_match.group(0) if email_match else ""
                    except Exception:
                        email = ""
                    if not email:
                        continue
                    if profile_url and profile_url in seen_profiles:
                        continue
                    if profile_url:
                        seen_profiles.add(profile_url)
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
                df = pd.DataFrame(results)
                csv_data = df.to_csv(index=False)
                return csv_data
            else:
                return "No results found."
        except Exception as e:
            if 'browser' in locals():
                await browser.close()
            return f"Error: {str(e)}"
