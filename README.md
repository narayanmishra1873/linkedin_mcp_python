# LinkedIn Comments Scraper MCP Server

A Model Context Protocol (MCP) server that scrapes LinkedIn post comments to extract email addresses and profile information.

## Features

- Scrapes LinkedIn post comments looking for email addresses
- Extracts user names, headlines, and profile URLs
- Returns data in CSV format
- Supports authentication via environment variables or parameters
- Built with FastMCP for easy hosting and integration

## Setup

### Environment Variables

Create a `.env` file in the root directory with your LinkedIn credentials:

```env
LINKEDIN_USERNAME=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password
```

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
    post_url="https://www.linkedin.com/posts/example-post-url",
    n=10
)

# Using provided credentials
result = await scrape_linkedin_post(
    post_url="https://www.linkedin.com/posts/example-post-url",
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
