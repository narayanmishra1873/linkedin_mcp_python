import os
import logging
import pandas as pd
import re
from playwright.async_api import async_playwright
from .linkedin_login import ensure_linkedin_login, STORAGE_STATE_PATH
import asyncio
import json
from google import genai

def _clean_profile_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    lines = raw_text.split('\n')
    cleaned_lines = []
    skip_to_search_found = False
    for line in lines:
        if not skip_to_search_found:
            if 'Skip to search' in line:
                skip_to_search_found = True
            continue
        cleaned_line = re.sub(r'\{.*?\}\s*', '', line, flags=re.DOTALL)
        if cleaned_line.strip():
            cleaned_lines.append(cleaned_line.strip())
        if 'InterestsInterests' in cleaned_line:
            break
    return "\n".join(cleaned_lines)

async def _extract_data_with_gemini(content: str, api_key: str) -> dict:
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
        response = await asyncio.to_thread(
            llm.models.generate_content,
            model=model,
            contents=prompt
        )
        raw_response = response.text.strip()
        if raw_response.startswith("```json") or raw_response.startswith("````"):
            raw_response = raw_response.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            validated_data = _validate_and_format_for_csv(data)
            return validated_data
        else:
            return None
    except Exception:
        return None

def _validate_and_format_for_csv(data: dict) -> dict:
    if not isinstance(data, dict):
        return _create_fallback_result()
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

async def extract_linkedin_profile_data(
    profile_url: str,
    username: str = None,
    password: str = None
) -> str:
    linkedin_username = username or os.getenv("LINKEDIN_USERNAME")
    linkedin_password = password or os.getenv("LINKEDIN_PASSWORD")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    logger = logging.getLogger(__name__)
    if not linkedin_username or not linkedin_password:
        return "Missing LinkedIn credentials. Please provide username and password parameters or set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables."
    if not google_api_key:
        return "Missing Google API key. Please set GOOGLE_API_KEY environment variable."
    logger.info(f"Starting LinkedIn profile data extraction")
    logger.info(f"Target profile URL: {profile_url}")
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
            logger.info(f"Navigating to profile: {profile_url}")
            await page.goto(profile_url)
            await page.wait_for_load_state()
            await asyncio.sleep(3)
            logger.info("Profile page loaded, extracting content...")
            try:
                page_text = await page.locator('body').text_content()
                logger.info("Successfully extracted page content")
            except Exception as e:
                logger.error(f"Error extracting page content: {e}")
                await browser.close()
                return f"Error extracting page content: {str(e)}"
            await browser.close()
            logger.info("Cleaning extracted text...")
            cleaned_text = _clean_profile_text(page_text)
            logger.info("Processing text with Gemini AI...")
            profile_data = await _extract_data_with_gemini(cleaned_text, google_api_key)
            if profile_data:
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
