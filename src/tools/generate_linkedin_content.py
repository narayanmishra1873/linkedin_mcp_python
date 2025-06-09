import os
import logging
from googlesearch import search
import json
from google import genai
from dotenv import load_dotenv
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import time

# Load environment variables
load_dotenv()

# Configure Google Gemini AI
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# System prompt for generating LinkedIn posts
LINKEDIN_POST_SYSTEM_PROMPT = """You are an elite LinkedIn content strategist who creates viral, thought-provoking posts for industry leaders. Your task is to analyze extracted LinkedIn posts and create ONE exceptional, ready-to-post LinkedIn post that drives massive engagement.

ANALYSIS REQUIREMENTS:
1. Deeply analyze the extracted LinkedIn posts to identify:
   - Emerging trends and breakthrough insights
   - Most successful storytelling patterns
   - Controversial or contrarian viewpoints that spark debate
   - Data points, statistics, or surprising facts
   - Personal experiences and real-world case studies
   - Industry pain points and innovative solutions

2. Create ONE premium LinkedIn post that:
   - Delivers exceptional professional value
   - Challenges conventional thinking
   - Shares actionable insights or frameworks
   - Tells a compelling story with a clear narrative arc
   - Positions the author as a visionary thought leader

CONTENT EXCELLENCE STANDARDS:
- Start with a POWERFUL hook that creates immediate curiosity or surprise
- 400-600 words (longer, richer content)
- Include specific examples, data, or case studies
- Share contrarian insights or challenge industry assumptions
- Provide actionable takeaways or frameworks
- Use storytelling techniques (problem → insight → solution → lesson)
- End with a thought-provoking question that sparks meaningful debate

ENGAGEMENT AMPLIFIERS:
- Bold, controversial, or contrarian statements (professionally appropriate)
- Personal anecdotes with universal business lessons
- Industry predictions with supporting evidence
- Frameworks, methodologies, or step-by-step processes
- Behind-the-scenes insights from successful companies/projects
- Data-driven observations with surprising conclusions

FORMATTING FOR VIRALITY:
- Strategic use of line breaks for mobile readability
- Bullet points or numbered lists for key insights
- Selective emoji usage for emphasis (not decoration)
- 5-7 strategic hashtags for maximum reach
- Professional yet authentic and conversational tone

OUTPUT REQUIREMENTS:
- Output ONLY the final LinkedIn post
- NO analysis, explanations, or meta-commentary
- Create content that stops the scroll and demands engagement
- Focus on delivering exceptional value that people want to share"""

def _scrape_linkedin_post_content(url: str) -> str:
    """
    Scrape the body text content from a LinkedIn post URL.
    
    Args:
        url (str): LinkedIn post URL
    
    Returns:
        str: Extracted body text from the post
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        logger.info(f"Scraping content from: {url}")
        
        # Send GET request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try different selectors to find post content
        post_content = ""
        
        # If no specific selectors work, try to extract from meta description
        if not post_content:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                post_content = meta_desc.get('content', '')
        
        # Fallback: extract from page title and visible text
        if not post_content:
            # Get page title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ""
            
            # Try to extract main content
            main_content = soup.find('main')
            if main_content:
                # Remove script and style elements
                for script in main_content(["script", "style"]):
                    script.decompose()
                post_content = main_content.get_text(strip=True)[:500]  # Limit to first 500 chars
            else:
                post_content = title_text
        
        logger.info(f"Extracted {len(post_content)} characters of content")
        return post_content
        
    except Exception as e:        
        logger.error(f"Error scraping LinkedIn post content: {str(e)}")
        return f"Error scraping content: {str(e)}"

def _generate_linkedin_posts_with_ai(extracted_content: str, topic: str = "", description: str = None) -> str:
    """
    Generate LinkedIn posts using Google Gemini AI based on extracted content.
    
    Args:
        extracted_content (str): The extracted LinkedIn posts content
        topic (str): Optional topic for focused content generation
        description (str): Optional description/feedback for content customization
    
    Returns:
        str: Generated LinkedIn posts
    """
    logger = logging.getLogger(__name__)
    
    if not GOOGLE_API_KEY:
        return "Error: GOOGLE_API_KEY not found in environment variables. Please add it to your .env file"
    
    try:
        # Initialize Gemini client
        llm = genai.Client(api_key=GOOGLE_API_KEY)
        model = "gemini-2.0-flash"
        
        # Create the prompt
        user_prompt = f"""
Based on the following extracted LinkedIn posts about {topic}, create ONE exceptional LinkedIn post that goes viral.

EXTRACTED CONTENT:
{extracted_content}

{f'''ADDITIONAL DESCRIPTION/FEEDBACK:
{description}

Please incorporate this feedback and direction into your post creation.
''' if description else ''}

Create a thought-provoking, insight-rich LinkedIn post that challenges conventional thinking and delivers massive value. Make it longer, deeper, and more engaging than typical posts. Include specific examples, actionable frameworks, and bold insights that position the author as a visionary thought leader.

Output only the final post - no analysis or commentary.
"""
        
        # Combine system prompt and user prompt
        full_prompt = LINKEDIN_POST_SYSTEM_PROMPT + "\n\n" + user_prompt
        
        logger.info("Generating LinkedIn posts with Google Gemini AI...")
        
        # Generate content using Gemini (synchronous call)
        response = llm.models.generate_content(
            model=model,
            contents=full_prompt
        )
        
        if response and hasattr(response, 'text') and response.text:
            logger.info("Successfully generated LinkedIn posts with AI")
            return response.text
        else:
            logger.error("No response received from Gemini AI")
            return "Error: No response received from AI model"
            
    except Exception as e:
        logger.error(f"Error generating LinkedIn posts with AI: {str(e)}")
        # More specific error handling
        if "getaddrinfo failed" in str(e):
            return "Error: Network connection failed. Please check your internet connection and try again."
        elif "API key" in str(e).lower():
            return "Error: Invalid or missing Google API key. Please check your GOOGLE_API_KEY environment variable."
        else:
            return f"Error generating AI content: {str(e)}"

async def generate_linkedin_content(
    subject: str, 
    num_posts: int = 10, 
    description: str = None
) -> str:
    """
    Extract LinkedIn posts about a subject and generate new AI-powered content.
    
    This tool searches for LinkedIn posts using Google search, extracts their content,
    and uses Google Gemini AI to generate a new engaging LinkedIn post based on the
    extracted data.
    
    Args:
        subject (str): The subject/topic to search for (e.g., "AI technology", "digital marketing")
        num_posts (int): Number of posts to extract for analysis (default: 10, max: 20)
        description (str): Optional description/feedback for content customization
    
    Returns:
        str: AI-generated LinkedIn post ready for publishing
    """
    logger = logging.getLogger(__name__)
    
    # Validate inputs
    if not subject or not subject.strip():
        return "Error: Subject is required. Please provide a topic to search for."
    
    if num_posts < 1 or num_posts > 20:
        return "Error: num_posts must be between 1 and 20."
    
    # Suppress logging for clean output in MCP context
    logging.getLogger().setLevel(logging.CRITICAL)
    
    logger.info(f"Searching for {num_posts} LinkedIn posts about: {subject}")
    
    try:
        # Search for LinkedIn posts
        search_query = f"site:linkedin.com/posts/ '{subject}'"
        search_results = search(search_query, num_results=num_posts, unique=True, advanced=True)
        
        # Convert generator to list
        results_list = list(search_results)
        if not results_list:
            return f"No LinkedIn posts found for subject: {subject}. Try a different search term."
        
        # Build content string
        content_parts = []
        content_parts.append(f"Subject: {subject}")
        content_parts.append(f"Number of Posts: {len(results_list)}")
        content_parts.append(f"Extracted at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        content_parts.append("=" * 80)
        content_parts.append("")
        
        successful_extractions = 0
        for i, post in enumerate(results_list, 1):
            logger.info(f"Processing post {i}/{len(results_list)}: {post.url}")
            
            # Scrape the post content
            post_content = _scrape_linkedin_post_content(post.url)
            
            if post_content and not post_content.startswith("Error"):
                content_parts.append(f"POST {i}")
                content_parts.append(f"URL: {post.url}")
                content_parts.append("-" * 60)
                content_parts.append(post_content)
                content_parts.append("")
                content_parts.append("=" * 80)
                content_parts.append("")
                successful_extractions += 1
            else:
                logger.warning(f"Failed to extract content from post {i}: {post.url}")
        
        # Join all content parts
        extracted_content = "\n".join(content_parts)
        
        if successful_extractions == 0:
            return f"Failed to extract content from any LinkedIn posts about '{subject}'. This may be due to LinkedIn's security measures or network issues."
        
        logger.info(f"Successfully extracted {successful_extractions}/{len(results_list)} posts")
        
        # Generate AI content
        logger.info("Generating AI content based on extracted posts...")
        ai_posts = _generate_linkedin_posts_with_ai(extracted_content, subject, description)
        
        if ai_posts and not ai_posts.startswith("Error"):
            return ai_posts
        else:
            return f"Successfully extracted {successful_extractions} posts, but failed to generate AI content. Error: {ai_posts}"
        
    except Exception as e:
        logger.error(f"Error in generate_linkedin_content: {str(e)}")
        if "HTTP 429" in str(e):
            return "Error: Rate limited by Google Search. Please wait a few minutes before trying again."
        elif "getaddrinfo failed" in str(e):
            return "Error: Network connection failed. Please check your internet connection."
        else:
            return f"Error: {str(e)}"
