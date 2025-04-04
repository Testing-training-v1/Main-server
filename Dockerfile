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

# Install dependencies with special handling for scientific packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools cython

# Install scientific packages first to ensure proper version resolution
RUN pip install --no-cache-dir --prefer-binary \
    numpy==1.24.4 \
    scipy==1.10.1 \
    pandas==2.0.3 \
    scikit-learn==1.1.3 \
    joblib==1.3.2

# Install remaining dependencies
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /tmp/data /tmp/models /tmp/nltk_data

# Install NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Verify installations
RUN python -c "import numpy; print(f'numpy version: {numpy.__version__}')" && \
    python -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')" && \
    python -c "import coremltools; print(f'coremltools version: {coremltools.__version__}')"

# Expose port
EXPOSE 10000

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run the application
CMD ["/entrypoint.sh"]
