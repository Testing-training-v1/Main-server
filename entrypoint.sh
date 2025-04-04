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
    mkdir -p ${RENDER_DISK_PATH}/data ${RENDER_DISK_PATH}/models ${RENDER_DISK_PATH}/nltk_data
fi

# Verify NLTK resources are installed
echo "Verifying NLTK resources..."
python -c "import nltk; nltk.data.path.append('/app/nltk_data'); [nltk.download(x) for x in ['punkt', 'stopwords', 'wordnet'] if not nltk.data.find(x)]"

# Run health check to verify scikit-learn is working
echo "Verifying scikit-learn installation..."
python -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')"

# Choose how to run the application based on environment
if [ -n "$GUNICORN_WORKERS" ]; then
    echo "Starting application with Gunicorn..."
    exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers ${GUNICORN_WORKERS:-2} "app:app"
else
    echo "Starting application with Flask development server..."
    exec python app.py
fi
