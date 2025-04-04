# Use Python 3.11 for compatibility with coremltools
FROM python:3.11.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /tmp/data /tmp/models /tmp/nltk_data

# Expose port
EXPOSE 10000

# Run the application
CMD ["python", "app.py"]
