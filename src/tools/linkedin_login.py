import os

STORAGE_STATE_PATH = "linkedin-state.json"

async def ensure_linkedin_login(page, linkedin_username, linkedin_password):
    await page.goto("https://www.linkedin.com/feed/")
    try:
        await page.wait_for_selector("input[aria-label='Search']", timeout=8000)
        return True
    except Exception:
        pass
    await page.goto("https://www.linkedin.com/login")
    await page.wait_for_selector("#username")
    await page.fill("#username", linkedin_username)
    await page.wait_for_selector("#password")
    await page.fill("#password", linkedin_password)
    await page.click("button[type='submit']")
    try:
        await page.wait_for_selector("input[aria-label='Search']", timeout=60000)
        context = page.context
        await context.storage_state(path=STORAGE_STATE_PATH)
        return True
    except Exception:
        return False
