#!/bin/bash
set -e

echo "Starting Backdoor AI Learning Server..."

# Check if we're running on a platform that requires environment setup
if [ -n "$KOYEB_DEPLOYMENT" ]; then
    echo "Running on Koyeb platform"
    export TMP_DIR=/tmp
    # Create required directories
    mkdir -p $TMP_DIR/data $TMP_DIR/models $TMP_DIR/nltk_data
elif [ -n "$RENDER" ]; then
    echo "Running on Render platform"
    # Directories should be in persistent volume already
fi

# Install NLTK resources to avoid runtime downloads
echo "Installing NLTK resources..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Run the application
echo "Starting application..."
exec python app.py
