#!/bin/bash
set -e

echo "Running Render build script..."

# Render doesn't allow apt-get installs during build (read-only filesystem)
# We'll rely on pre-built wheels and Render's Python environment

# Upgrade pip and install wheel/setuptools first
pip install --upgrade pip setuptools wheel cython

# Install Python dependencies with binary preference
# Force binary packages where possible to avoid compilation issues
pip install --prefer-binary --only-binary=numpy,scipy,scikit-learn -r requirements.txt

# Verify critical packages installed correctly
python -c "import numpy; print(f'numpy version: {numpy.__version__}')"
python -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')"
python -c "import nltk; print(f'nltk version: {nltk.__version__}')"

# Prepare NLTK data
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True)"

# Make the entrypoint executable
chmod +x entrypoint.sh

echo "Build completed successfully"
