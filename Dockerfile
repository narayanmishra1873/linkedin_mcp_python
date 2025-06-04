FROM python:3.11-slim

WORKDIR /app
# Install system dependencies for Playwright and other requirements
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory


# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (after MCP is installed)
RUN playwright install --with-deps chromium

# Copy application code
COPY src/ ./src/
COPY .env* ./

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0

# Run the application using FastMCP's built-in streamable-http transport
CMD ["python", "src/server.py"]
