# LinkedIn Automation & Content Generation Tool 🚀

A comprehensive LinkedIn automation tool that combines MCP (Model Context Protocol) server functionality with AI-powered content generation. The tool extracts LinkedIn posts via Google search, scrapes their content, and uses Google Gemini AI to generate new engaging posts based on the extracted data.

## Features ✨

### Core LinkedIn Tools (MCP Server)
- **🔍 Health Check**: Monitor server status and connectivity
- **📄 Post Scraping**: Extract LinkedIn post content and comments
- **👤 Profile Extraction**: Get detailed LinkedIn profile data
- **🏢 Company Employees**: Extract employee lists from company pages
- **🤝 Connection Requests**: Automated connection request sending

### NEW: AI Content Generation
- **🔍 Smart Post Extraction**: Searches for LinkedIn posts using Google search with `site:linkedin.com/posts/`
- **📄 Web Scraping**: Extracts post content without requiring LinkedIn login
- **🤖 AI Content Generation**: Uses Google Gemini AI to create engaging LinkedIn posts
- **📊 Analytics**: Tracks extraction success rates and content analysis
- **🎯 Topic-Focused**: Search for posts about specific subjects or industries

## Setup

### Environment Variables

Create a `.env` file in the root directory with your credentials:

```env
# LinkedIn credentials (for MCP server tools)
LINKEDIN_USERNAME=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Google Gemini AI API Key (for content generation)
# Get your API key from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage 🎯

### 1. AI Content Generation (NEW!)

#### Quick Demo
```python
python extract_linkedin_post.py
```

#### Custom Subject Search
```python
from extract_linkedin_post import demo_linkedin_automation

# Extract posts about AI and generate new content
demo_linkedin_automation("artificial intelligence", num_posts=5)
```

#### Advanced Usage - Extract and Generate Posts
```python
from extract_linkedin_post import extract_and_generate_posts

results = extract_and_generate_posts(
    subject="machine learning",
    num_posts=10,
    generate_ai_content=True
)

print("Extracted Content:", results["extracted_content"])
print("AI Generated Posts:", results["ai_generated_posts"])
print("Summary:", results["summary"])
```

### 2. MCP Server Tools

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

### Running Locally

```bash
python src/server.py
```

The server will start with SSE transport for MCP communication.

## Docker Deployment

### Build the Docker image:
```bash
docker build -t linkedin-scraper-mcp .
```

### Run the container:
```bash
docker run -p 8000:8000 --env-file .env linkedin-scraper-mcp
```

## Usage

The server provides one main tool:

### `scrape_linkedin_post`

Scrapes a LinkedIn post for comments containing email addresses.

**Parameters:**
- `post_url` (string, required): The LinkedIn post URL to scrape
- `n` (integer, optional): Maximum number of results to return (default: 20)
- `username` (string, optional): LinkedIn username/email (falls back to env var)
- `password` (string, optional): LinkedIn password (falls back to env var)

**Returns:**
CSV formatted string with columns: name, headline, profile_url, email

**Example:**
```python
# Using environment variables for credentials
result = await scrape_linkedin_post(
    post_url="https://www.linkedin.com/posts/mishra-narayan_kgpians-placements-jobopportunities-activity-7113220698688385025-c0w0/",
    n=10
)

# Using provided credentials
result = await scrape_linkedin_post(
    post_url="https://www.linkedin.com/posts/mishra-narayan_kgpians-placements-jobopportunities-activity-7113220698688385025-c0w0/",
    n=10,
    username="your_email@example.com",
    password="your_password"
)
```

## How it Works

1. **Authentication**: Logs into LinkedIn using provided credentials
2. **Navigation**: Goes to the specified post URL
3. **Scraping**: Extracts comment entities and looks for:
   - User names and headlines
   - Profile URLs
   - Email addresses in comment text using regex
4. **Filtering**: 
   - Only includes comments with email addresses
   - Removes duplicate profiles
   - Skips reply comments (starting with '@')
5. **Load More**: Automatically clicks "Load more comments" to get additional results
6. **Output**: Returns data in CSV format

## Security Notes

- LinkedIn credentials are handled securely through environment variables
- The scraper respects LinkedIn's structure and doesn't overload their servers
- Uses appropriate delays between actions
- Runs in headless mode for production deployment

## Limitations

- Requires valid LinkedIn credentials
- Subject to LinkedIn's rate limiting and anti-bot measures
- May need updates if LinkedIn changes their HTML structure
- Browser automation may be detected by LinkedIn's security systems

## Troubleshooting

- **Login Failed**: Check your LinkedIn credentials and ensure 2FA is disabled for automation
- **No Results**: The post may not have comments with email addresses, or LinkedIn may have changed their structure
- **Browser Issues**: Ensure Playwright browsers are properly installed

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational and research purposes. Please respect LinkedIn's Terms of Service and use responsibly.
