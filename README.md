# LinkedIn Automation & Content Generation MCP Server 🚀

A comprehensive **AI-powered LinkedIn automation platform** built on the Model Context Protocol (MCP) architecture. This sophisticated system combines advanced AI content generation, browser automation, and business intelligence extraction to provide a complete LinkedIn automation suite for content creators, marketers, sales professionals, and business development teams.

## 🌟 Key Features

### 🤖 AI-Powered Content Generation
- **Smart Content Creation**: Generate viral LinkedIn posts using Google Gemini AI
- **Topic Research**: Analyze existing LinkedIn content for trending topics and insights
- **Engagement Optimization**: Create posts optimized for maximum engagement and reach
- **Content Strategy**: Professional storytelling frameworks and thought leadership positioning

### 📊 Business Intelligence & Analytics
- **🏢 Company Analysis**: Extract comprehensive employee data from LinkedIn companies
- **👤 Profile Intelligence**: Deep profile data extraction with AI-powered insights
- **📈 Market Research**: Competitive analysis and industry intelligence gathering
- **🎯 Lead Generation**: Automated prospect identification and data collection

### 🤝 Sales & Networking Automation
- **🔗 Connection Automation**: Send personalized connection requests at scale
- **� AI Personalization**: Generate custom messages based on profile analysis
- **📱 Outreach Management**: Streamlined LinkedIn outreach workflows
- **🎯 Targeted Networking**: Strategic connection building based on company and role targeting

### 🛠️ Technical & Operational
- **⚡ Health Monitoring**: Comprehensive server health checks and status monitoring
- **� Multi-Deployment**: MCP server, standalone, and cloud deployment options
- **🐳 Docker Ready**: Complete containerization for cloud deployment
- **🔒 Session Management**: Persistent LinkedIn authentication and state management

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key ([Get yours here](https://aistudio.google.com/app/apikey))
- LinkedIn account credentials
- Chrome/Chromium browser (automatically handled by Playwright)

### Environment Setup

Create a `.env` file in the root directory:

```env
# LinkedIn Authentication (Required for all LinkedIn tools)
LINKEDIN_USERNAME=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Google Gemini AI API Key (Required for AI content generation)
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd linkedin_mcp_python

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## 💡 Usage Examples

### 1. MCP Server Mode (Recommended)
**For use with Claude Desktop or other MCP clients**

```bash
# Start the MCP server
python src/server.py
```

Connect via MCP client and use these tools:
- `health_check` - Verify server status
- `generate_linkedin_content` - Create AI-powered viral posts
- `extract_linkedin_profile_data` - Get comprehensive profile insights
- `extract_company_employees` - Analyze company employee data
- `send_connection_request` - Automate personalized outreach
- `scrape_linkedin_post` - Extract post content and engagement data

### 2. Cloud Deployment Mode
**For production hosting (Render, Heroku, etc.)**

```bash
# Using uvicorn for better cloud compatibility
python src/main.py
```

### 3. Standalone Content Generation
**Quick AI content generation without MCP setup**

```bash
# Generate LinkedIn content directly
python PostLinkedin.py
```

## 🎯 Tool Descriptions

### `generate_linkedin_content`
**AI-Powered Content Generation**
- Searches LinkedIn for posts on your topic
- Analyzes content patterns and engagement factors
- Generates viral, thought-provoking posts using Google Gemini AI
- Optimizes for professional engagement and thought leadership

**Parameters:**
- `topic` (required): Subject or industry to generate content about
- `num_posts` (optional): Number of posts to analyze (default: 10)

**Example Output:**
Creates 400-600 word LinkedIn posts with:
- Compelling hooks and storytelling
- Industry insights and contrarian viewpoints
- Actionable frameworks and takeaways
- Engagement-optimized formatting

### `extract_linkedin_profile_data`
**Comprehensive Profile Intelligence**
- Extracts complete professional profile information
- AI-powered data structuring and analysis
- Contact information and professional history
- Skills, endorsements, and activity insights

**Parameters:**
- `profile_url` (required): LinkedIn profile URL

**Use Cases:**
- Sales prospecting and lead qualification
- Recruitment candidate evaluation
- Market research and competitive analysis

### `extract_company_employees`
**Company Intelligence & Employee Mapping**
- Extracts employee lists from company pages
- Prioritizes high-designation roles (C-level, VPs, Directors)
- Comprehensive employee profile data
- Organizational structure insights

**Parameters:**
- `company_input` (required): Company name or LinkedIn company URL

**Business Applications:**
- Competitive intelligence
- Sales territory mapping
- Recruitment sourcing
- Partnership development

### `send_connection_request`
**Automated Relationship Building**
- Sends personalized connection requests
- AI-generated personalized messages
- Integration with profile analysis for better targeting
- Compliance with LinkedIn messaging limits

**Parameters:**
- `profile_url` (required): Target LinkedIn profile
- `message` (optional): Custom message (max 180 characters)

**Smart Features:**
- Auto-generates personalized messages if none provided
- Uses profile data for contextual personalization
- Respects LinkedIn rate limits and best practices

## 🏗️ Architecture & Deployment

### Multi-Deployment Architecture
This platform supports three deployment modes for maximum flexibility:

1. **MCP Server Mode** (`src/server.py`) - Primary mode for MCP client integration
2. **Cloud Server Mode** (`src/main.py`) - Enhanced uvicorn server for cloud deployment
3. **Standalone Mode** (`PostLinkedin.py`) - Direct LinkedIn posting without MCP

### Docker Deployment

**Build and run with Docker:**
```bash
# Build the container
docker build -t linkedin-automation-mcp .

# Run with environment file
docker run -p 8000:8000 --env-file .env linkedin-automation-mcp
```

**Cloud Platform Deployment:**
- **Render.com**: Ready for one-click deployment
- **Heroku**: Full compatibility with Procfile configuration
- **AWS/GCP/Azure**: Container-ready for major cloud platforms

### Technology Stack
- **Backend**: Python 3.11+, FastMCP, Uvicorn
- **Browser Automation**: Playwright with Chromium
- **AI Integration**: Google Gemini AI with advanced prompting
- **Search**: Google Search Python library
- **Data Processing**: Pandas, BeautifulSoup4
- **Containerization**: Docker with multi-stage builds

## 🔧 Advanced Configuration

### Environment Variables
```env
# Required - LinkedIn Authentication
LINKEDIN_USERNAME=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Required - AI Content Generation
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional - Server Configuration
HOST=0.0.0.0
PORT=8000

# Optional - Browser Configuration
HEADLESS=true
BROWSER_TIMEOUT=30000
```

### MCP Client Configuration
For Claude Desktop integration, add to your MCP configuration:

```json
{
  "mcpServers": {
    "linkedin-automation": {
      "command": "python",
      "args": ["path/to/linkedin_mcp_python/src/server.py"],
      "env": {
        "LINKEDIN_USERNAME": "your_username",
        "LINKEDIN_PASSWORD": "your_password",
        "GOOGLE_API_KEY": "your_api_key"
      }
    }
  }
}
```

## 🎯 Business Use Cases

### Content Marketing Teams
- **AI Content Creation**: Generate viral LinkedIn posts optimized for engagement
- **Trend Analysis**: Research trending topics and successful content patterns
- **Content Strategy**: Develop thought leadership positioning and messaging

### Sales & Business Development
- **Lead Generation**: Extract qualified prospects from target companies
- **Outreach Automation**: Send personalized connection requests at scale
- **Account Intelligence**: Comprehensive company and employee analysis

### Recruitment & Talent Acquisition
- **Candidate Sourcing**: Find and analyze potential candidates by company/role
- **Talent Mapping**: Understand organizational structures and key personnel
- **Outreach Campaigns**: Automated, personalized candidate engagement

### Market Research & Intelligence
- **Competitive Analysis**: Analyze competitor employee structures and strategies
- **Industry Insights**: Extract market intelligence from LinkedIn activity
- **Partnership Development**: Identify potential partners and key decision makers

## 🛡️ Security & Compliance

### Best Practices
- **Credential Security**: Environment-based credential management
- **Rate Limiting**: Built-in safeguards to respect LinkedIn's usage policies
- **Session Management**: Secure authentication state persistence
- **Data Privacy**: GDPR-compliant data handling and processing

### LinkedIn Compliance
- Respects LinkedIn's Terms of Service
- Implements appropriate delays and rate limiting
- Uses headless browsing for production environments
- Handles anti-bot detection gracefully

## 📊 Performance & Monitoring

### Health Monitoring
- Built-in health check endpoints
- Comprehensive system status reporting
- Browser automation health verification
- AI service connectivity monitoring

### Performance Optimization
- Async/await patterns for concurrent operations
- Efficient browser session management
- Intelligent retry logic for network failures
- Memory-optimized data processing

## 🚨 Troubleshooting

### Common Issues
**Authentication Failures:**
- Verify LinkedIn credentials in `.env` file
- Disable 2FA for automation account
- Check for LinkedIn account restrictions

**Browser Automation Issues:**
- Ensure Playwright browsers are installed: `playwright install chromium`
- Check system dependencies for headless browser operation
- Verify Docker container has necessary browser dependencies

**AI Content Generation Problems:**
- Validate Google Gemini API key and quota
- Check internet connectivity for API calls
- Review API usage limits and billing status

**Performance Issues:**
- Monitor system resources (CPU, memory)
- Adjust browser timeout settings
- Implement connection pooling for high-volume usage

## 🤝 Contributing

We welcome contributions! Please see our contribution guidelines:

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black src/
isort src/
```

## 📄 License & Disclaimer

This project is designed for legitimate business use cases including marketing, sales, and recruitment. Users are responsible for:

- Complying with LinkedIn's Terms of Service
- Respecting data privacy and GDPR requirements
- Using automation responsibly and ethically
- Obtaining necessary permissions for data processing

**Disclaimer**: This tool is for educational and business purposes. Please use responsibly and in compliance with all applicable terms of service and regulations.

---

## 🎉 Get Started Today

Ready to transform your LinkedIn strategy with AI-powered automation?

1. **Clone the repository**
2. **Set up your environment variables**
3. **Install dependencies**
4. **Start generating viral content and automating outreach!**

For support and questions, please open an issue on GitHub or contact our team.

**Experience the future of LinkedIn automation and AI-powered content generation!** 🚀
