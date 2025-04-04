# Use Python 3.11 for compatibility with coremltools
FROM python:3.11.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    libatlas-base-dev \
    gfortran \
    libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies with special handling for scikit-learn
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools cython && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /tmp/data /tmp/models /tmp/nltk_data

# Install NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Expose port
EXPOSE 10000

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run the application
CMD ["/entrypoint.sh"]
