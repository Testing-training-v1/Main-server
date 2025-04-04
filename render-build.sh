#!/bin/bash
set -e

echo "Running Render build script..."

# Install system dependencies
apt-get update
apt-get install -y --no-install-recommends $(cat apt-dependencies.txt)

# Upgrade pip and install wheel/setuptools first
pip install --upgrade pip setuptools wheel

# Install Python dependencies with binary preference
pip install --prefer-binary -r requirements.txt

# Make the entrypoint executable
chmod +x entrypoint.sh

echo "Build completed successfully"
